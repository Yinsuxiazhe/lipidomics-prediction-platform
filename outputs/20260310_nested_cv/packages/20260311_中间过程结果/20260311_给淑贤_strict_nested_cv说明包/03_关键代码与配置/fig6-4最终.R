# ==============================================================================
# Figure 6-4 Honest Nested CV Version
# ------------------------------------------------------------------------------
# 目标：
# 1. 不再在 R 里重新做全样本插补/特征筛选/建模，避免信息泄漏；
# 2. 直接消费 Python strict nested CV pipeline 产物；
# 3. 输出“诚实口径”的 Figure 6-4：ROC + 泛化差距 + 特征稳定性。
# ------------------------------------------------------------------------------
# 运行方式：
#   Rscript fig6-4最终.R
#   Rscript fig6-4最终.R --rerun
# ------------------------------------------------------------------------------
# 主要输入：
#   outputs/20260310_nested_cv/performance_summary.csv
#   outputs/20260310_nested_cv/roc_curve_points.csv
#   outputs/20260310_nested_cv/fold_metrics.csv
#   outputs/20260310_nested_cv/feature_stability_summary.csv
# ------------------------------------------------------------------------------
# 主要输出：
#   outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png
#   outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf
# ==============================================================================

suppressPackageStartupMessages(suppressWarnings({
  library(ggplot2)
  library(dplyr)
  library(readr)
  library(tidyr)
  library(patchwork)
}))

args <- commandArgs(trailingOnly = TRUE)
rerun_pipeline <- "--rerun" %in% args

get_script_dir <- function() {
  file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_arg) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg[1]))))
  }
  normalizePath(getwd())
}

project_root <- get_script_dir()
output_dir <- file.path(project_root, "outputs", "20260310_nested_cv")
if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE)

required_files <- c(
  file.path(output_dir, "performance_summary.csv"),
  file.path(output_dir, "roc_curve_points.csv"),
  file.path(output_dir, "fold_metrics.csv"),
  file.path(output_dir, "feature_stability_summary.csv")
)

ensure_strict_outputs <- function(force = FALSE) {
  missing_files <- required_files[!file.exists(required_files)]
  if (!force && length(missing_files) == 0) {
    return(invisible(TRUE))
  }

  message("正在运行 strict nested CV pipeline ...")
  current_wd <- getwd()
  on.exit(setwd(current_wd), add = TRUE)
  setwd(project_root)

  cmd <- c("run_pipeline.py", "--stage", "experiments", "--config", "config/analysis.yaml")
  status <- system2("python3", cmd)
  if (!identical(status, 0L)) {
    stop("Python strict nested CV pipeline 运行失败，请先检查 run_pipeline.py。")
  }

  missing_after <- required_files[!file.exists(required_files)]
  if (length(missing_after) > 0) {
    stop(paste0("缺少必要输出文件：", paste(basename(missing_after), collapse = ", ")))
  }

  invisible(TRUE)
}

ensure_strict_outputs(force = rerun_pipeline)

performance <- read_csv(file.path(output_dir, "performance_summary.csv"), show_col_types = FALSE)
roc_points <- read_csv(file.path(output_dir, "roc_curve_points.csv"), show_col_types = FALSE)
fold_metrics <- read_csv(file.path(output_dir, "fold_metrics.csv"), show_col_types = FALSE)
stability <- read_csv(file.path(output_dir, "feature_stability_summary.csv"), show_col_types = FALSE)

label_map <- c(
  clinical_slim_logistic = "Clinical baseline",
  clinical_full_elastic_net = "Expanded clinical",
  lipid_elastic_net = "Lipid-only",
  fusion_elastic_net = "Clinical + lipid fusion",
  fusion_full_elastic_net = "Expanded fusion"
)

pretty_feature_name <- function(x) {
  named <- c(
    age_enroll = "Age",
    bmi_z_enroll = "BMI z-score",
    BMI = "BMI",
    SFT = "Chest skinfold thickness (SFT)",
    Gender = "Sex",
    whole_blood_LYMPH_count = "Whole-blood lymphocyte count"
  )
  out <- ifelse(x %in% names(named), named[x], x)
  unname(out)
}

classify_feature_type <- function(x) {
  clinical_features <- c(
    "age_enroll", "bmi_z_enroll", "BMI", "SFT", "Gender",
    "whole_blood_LYMPH_count", "whole_blood_MONO_count", "whole_blood_NEUT_count",
    "FPG", "ALT", "AST", "TG", "TC", "HDL_C", "LDL_C"
  )
  ifelse(x %in% clinical_features, "Clinical", "Lipid")
}

performance <- performance %>%
  mutate(
    display = unname(label_map[experiment]),
    display = ifelse(is.na(display), experiment, display),
    generalization_gap = mean_train_auc - mean_auc
  )

roc_points <- roc_points %>%
  mutate(
    display = unname(label_map[experiment]),
    display = ifelse(is.na(display), experiment, display)
  )

fold_metrics <- fold_metrics %>%
  mutate(
    display = unname(label_map[experiment]),
    display = ifelse(is.na(display), experiment, display)
  )

stability <- stability %>%
  mutate(
    display = unname(label_map[experiment]),
    display = ifelse(is.na(display), experiment, display),
    feature_pretty = pretty_feature_name(feature),
    feature_type = classify_feature_type(feature)
  )

pair_configs <- list(
  list(
    experiments = c("clinical_slim_logistic", "clinical_full_elastic_net"),
    title = "A. Clinical baseline",
    colors = c("#BC3C29", "#0072B5"),
    summary_labels = c("Baseline", "Expanded")
  ),
  list(
    experiments = c("clinical_full_elastic_net", "fusion_full_elastic_net"),
    title = "B. Added lipidomics",
    colors = c("#0072B5", "#E18727"),
    summary_labels = c("Clinical", "Fusion")
  ),
  list(
    experiments = c("fusion_elastic_net", "fusion_full_elastic_net"),
    title = "C. Fusion model comparison",
    colors = c("#E18727", "#20854E"),
    summary_labels = c("Fusion", "Expanded")
  )
)

build_auc_text <- function(experiments, summary_labels) {
  rows <- performance %>%
    filter(experiment %in% experiments) %>%
    mutate(order_id = match(experiment, experiments)) %>%
    arrange(order_id)

  paste(
    sprintf("%s: %.3f ± %.3f", summary_labels, rows$mean_auc, rows$std_auc),
    collapse = "\n"
  )
}

build_roc_panel <- function(cfg) {
  display_levels <- unname(label_map[cfg$experiments])
  df <- roc_points %>%
    filter(experiment %in% cfg$experiments) %>%
    mutate(display = factor(display, levels = display_levels))

  auc_text <- build_auc_text(cfg$experiments, cfg$summary_labels)
  color_values <- stats::setNames(cfg$colors, display_levels)

  ggplot(df, aes(x = fpr, y = tpr, color = display)) +
    geom_path(linewidth = 1.1) +
    geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "gray70") +
    coord_equal() +
    scale_color_manual(values = color_values) +
    labs(
      title = cfg$title,
      x = "False positive rate",
      y = "True positive rate",
      color = NULL
    ) +
    annotate(
      "label",
      x = 0.04,
      y = 0.96,
      label = auc_text,
      hjust = 0,
      vjust = 1,
      size = 3.0,
      fill = "white",
      alpha = 0.92
    ) +
    theme_bw(base_size = 11) +
    theme(
      legend.position = c(0.70, 0.16),
      legend.background = element_rect(fill = "white", color = NA),
      plot.title = element_text(face = "bold")
    )
}

plot_gap <- fold_metrics %>%
  filter(experiment %in% names(label_map)) %>%
  mutate(display = factor(display, levels = c(
    "Clinical baseline", "Expanded clinical", "Lipid-only",
    "Clinical + lipid fusion", "Expanded fusion"
  ))) %>%
  pivot_longer(
    cols = c(auc, train_auc),
    names_to = "metric",
    values_to = "auc_value"
  ) %>%
  mutate(metric = recode(metric, auc = "Outer test AUC", train_auc = "Train AUC")) %>%
  ggplot(aes(x = display, y = auc_value, fill = metric)) +
  geom_boxplot(
    position = position_dodge(width = 0.72),
    width = 0.62,
    outlier.shape = NA,
    alpha = 0.9
  ) +
  geom_point(
    aes(color = metric),
    position = position_jitterdodge(jitter.width = 0.08, dodge.width = 0.72),
    size = 1.6,
    alpha = 0.8,
    show.legend = FALSE
  ) +
  scale_fill_manual(values = c("Outer test AUC" = "#3C5488", "Train AUC" = "#F39B7F")) +
  scale_color_manual(values = c("Outer test AUC" = "#3C5488", "Train AUC" = "#F39B7F")) +
  labs(
    title = "D. Fold-level generalization gap",
    x = NULL,
    y = "AUC",
    fill = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    axis.text.x = element_text(angle = 25, hjust = 1),
    plot.title = element_text(face = "bold")
  )

feature_panel_data <- stability %>%
  filter(experiment == "fusion_full_elastic_net") %>%
  arrange(desc(selection_rate), rank) %>%
  slice_head(n = 12) %>%
  mutate(feature_pretty = factor(feature_pretty, levels = rev(feature_pretty)))

plot_feature <- ggplot(feature_panel_data, aes(x = selection_rate, y = feature_pretty, fill = feature_type)) +
  geom_col(width = 0.68) +
  scale_fill_manual(values = c("Clinical" = "#4DBBD5", "Lipid" = "#00A087")) +
  labs(
    title = "E. Stable features in expanded fusion model",
    x = "Selection rate across outer folds",
    y = NULL,
    fill = NULL
  ) +
  xlim(0, 1) +
  theme_bw(base_size = 11) +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = c(0.78, 0.14),
    legend.background = element_rect(fill = "white", color = NA)
  )

p_a <- build_roc_panel(pair_configs[[1]])
p_b <- build_roc_panel(pair_configs[[2]])
p_c <- build_roc_panel(pair_configs[[3]])

layout <- "
ABC
DDE
"

final_plot <- p_a + p_b + p_c + plot_gap + plot_feature +
  plot_layout(design = layout) +
  plot_annotation(
    title = "Figure 6-4. Honest nested-CV evaluation of the lipidomics prediction workflow",
    subtitle = paste(
      "All ROC curves are based on aggregated outer-fold test predictions from strict nested CV.",
      "Feature screening, scaling, and model tuning were restricted to training folds.",
      sep = " "
    ),
    caption = paste(
      "Interpretation: lower AUCs than the old figure mean the previous workflow was optimistic,",
      "not that the strict analysis is wrong. This version prioritizes generalizability over headline scores.",
      sep = " "
    )
  )

png_file <- file.path(output_dir, "Figure6-4_Honest_NestedCV.png")
pdf_file <- file.path(output_dir, "Figure6-4_Honest_NestedCV.pdf")

ggsave(png_file, final_plot, width = 16, height = 10, dpi = 300)
ggsave(pdf_file, final_plot, width = 16, height = 10)

message("✅ Honest nested-CV Figure 6-4 已生成：")
message("   ", png_file)
message("   ", pdf_file)
