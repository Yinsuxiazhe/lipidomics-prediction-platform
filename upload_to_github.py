#!/usr/bin/env python3
"""
将本地 Git 仓库内容通过 GitHub REST API 上传到指定仓库。
策略：第一个文件用 PUT /contents 初始化仓库（这是 GitHub 允许在空仓库上做的唯一操作），
之后的文件用 POST /git/trees 批量追加。
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

REPO = "Yinsuxiazhe/lipidomics-prediction-platform"
BRANCH = "main"


def gh_rest(method: str, path: str, data=None) -> dict:
    """通过 gh auth token 发送 REST 请求。"""
    token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        f"https://api.github.com/{path.lstrip('/')}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {err_body}") from e


def is_repo_empty() -> bool:
    """检查仓库是否为空（无 commit）。"""
    try:
        gh_rest("GET", f"repos/{REPO}/git/refs/heads/{BRANCH}")
        return False
    except RuntimeError as e:
        if "409" in str(e) and "empty" in str(e).lower():
            return True
        raise


def get_files_to_upload(root: str) -> list[tuple[str, str]]:
    """返回 [(relative_path, bytes_content)] 列表。"""
    EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".streamlit",
                     "node_modules", ".playwright-cli", "parquet_cache",
                     "20260305_淑贤线上汇报过程记录"}
    EXCLUDE_EXTS = {".pkl", ".png", ".jpg", ".jpeg", ".pdf", ".zip",
                     ".gif", ".mp4", ".log", ".DS_Store"}
    LARGE_SKIP = 2 * 1024 * 1024  # > 2MB 跳过

    SKIP_Basenames = {"_output_", "metFIB", "MetFIB", ".meta.json",
                      "20260312_建议"}
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.startswith("._"):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXCLUDE_EXTS:
                continue
            if any(fn.startswith(s) for s in SKIP_Basenames):
                continue
            # 跳过 outputs/20260312_建议 整个目录
            if "20260312_建议" in dirpath:
                continue
            full = os.path.join(dirpath, fn)
            size = os.path.getsize(full)
            if size > LARGE_SKIP:
                print(f"  SKIP (large): {os.path.relpath(full, root)} ({size//1024:.0f} KB)")
                continue
            rel = os.path.relpath(full, root)
            with open(full, "rb") as f:
                content = f.read()
            files.append((rel, content))
    return files


def upload_single_file(path: str, content: bytes, message: str) -> str:
    """用 PUT /contents 在空仓库上创建第一个 commit。返回 commit SHA。"""
    encoded = base64.b64encode(content).decode()
    result = gh_rest("PUT", f"repos/{REPO}/contents/{path}", {
        "message": message,
        "content": encoded,
        "branch": BRANCH,
    })
    return result["commit"]["sha"]


def upload_batch(files: list[tuple[str, str]], base_commit_sha: str, message: str) -> str:
    """用 POST /git/trees 在已有 commit 的仓库上追加文件。"""
    # 上传所有 blob
    tree_items = []
    for path, content in files:
        encoded = base64.b64encode(content).decode()
        blob = gh_rest("POST", f"repos/{REPO}/git/blobs", {
            "content": encoded,
            "encoding": "base64",
        })
        tree_items.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })

    # 获取当前提交的 tree SHA
    current = gh_rest("GET", f"repos/{REPO}/git/commits/{base_commit_sha}")

    # 创建新树
    tree = gh_rest("POST", f"repos/{REPO}/git/trees", {
        "base_tree": current["tree"]["sha"],
        "tree": tree_items,
    })

    # 创建新提交
    commit = gh_rest("POST", f"repos/{REPO}/git/commits", {
        "message": message,
        "tree": tree["sha"],
        "parents": [base_commit_sha],
    })

    # 更新分支指针
    gh_rest("PATCH", f"repos/{REPO}/git/refs/heads/{BRANCH}", {
        "sha": commit["sha"],
        "force": False,
    })

    return commit["sha"]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="上传本地文件到 GitHub 仓库")
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--branch", default=BRANCH)
    parser.add_argument("--message", default="Initial commit")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    # 确认仓库可访问
    try:
        gh_rest("GET", f"repos/{args.repo}")
        print(f"✓ 仓库 {args.repo} 可访问")
    except Exception as e:
        print(f"✗ 仓库不存在或无权访问: {e}")
        sys.exit(1)

    # 扫描文件
    root = "."
    print("扫描文件（跳过 .pkl/.csv/.png/.pdf/.zip 等大文件）...")
    files = get_files_to_upload(root)
    print(f"共 {len(files)} 个文件待上传\n")

    if not files:
        print("没有文件需要上传。")
        return

    # 确认仓库是否为空
    empty = is_repo_empty()
    print(f"仓库状态：{'空（将初始化）' if empty else '已有内容（将追加）'}")

    if empty:
        # 第一步：用第一个文件初始化仓库
        first_path, first_content = files[0]
        first_msg = args.message
        print(f"[初始化] 上传第一个文件: {first_path}")
        try:
            current_sha = upload_single_file(first_path, first_content, first_msg)
            print(f"  ✓ 仓库已初始化，commit SHA: {current_sha[:8]}")
        except Exception as e:
            print(f"  ✗ 初始化失败: {e}")
            sys.exit(1)
        remaining = files[1:]
    else:
        # 获取当前分支 commit SHA
        ref = gh_rest("GET", f"repos/{REPO}/git/refs/heads/{BRANCH}")
        current_sha = ref["object"]["sha"]
        remaining = files

    # 后续文件分批上传
    total = len(remaining)
    for i in range(0, total, args.batch_size):
        batch = remaining[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        msg = args.message if i == 0 else f"Upload batch {batch_num} (files {i+1}–{min(i+args.batch_size, total)})"
        print(f"\n[{i+1}–{min(i+args.batch_size, total)}/{total}] 上传中...")
        try:
            current_sha = upload_batch(batch, current_sha, msg)
            print(f"  ✓ commit {current_sha[:8]}")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            sys.exit(1)

    print(f"\n✓ 全部完成！访问 https://github.com/{args.repo}")


if __name__ == "__main__":
    main()
