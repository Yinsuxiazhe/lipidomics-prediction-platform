import {
  DEFAULT_PLUGIN_PARAMS,
  PARAM_FIELDS,
  normalizeParamValue,
} from "../config/claudeCodeTerminalDefaults.js";
import { ClaudeCodeTerminalScene } from "../scenes/ClaudeCodeTerminalScene.jsx";
import {
  resolveSceneContext,
  getDurationInFrames,
  buildSceneProps,
} from "../scenes/claudeCodeTerminalSceneBuilder.js";

export const claudeCodeTerminalPlugin = Object.freeze({
  id: "claude-code-terminal",
  controlPanelTitle: "Claude Code Terminal",
  controlPanelDescription: "Animated Claude Code CLI typing effect.",
  paramFields: PARAM_FIELDS,
  defaultProps: DEFAULT_PLUGIN_PARAMS,
  SceneComponent: ClaudeCodeTerminalScene,
  normalizeParamValue: ({ key, rawValue, currentValue }) =>
    normalizeParamValue({ key, rawValue, currentValue }),
  resolveSceneContext: (pluginParams) =>
    resolveSceneContext({ ...DEFAULT_PLUGIN_PARAMS, ...(pluginParams ?? {}) }),
  getDurationInFrames: ({ fps, sceneContext, pluginParams }) =>
    getDurationInFrames({
      fps,
      sceneContext: sceneContext ?? resolveSceneContext({ ...DEFAULT_PLUGIN_PARAMS, ...(pluginParams ?? {}) }),
    }),
  buildSceneProps: ({ frame, fps, loop, sceneContext, pluginParams }) =>
    buildSceneProps({
      frame,
      fps,
      loop,
      sceneContext: sceneContext ?? resolveSceneContext({ ...DEFAULT_PLUGIN_PARAMS, ...(pluginParams ?? {}) }),
    }),
  getLayout: ({ sceneContext, pluginParams }) => {
    const ctx = sceneContext ?? resolveSceneContext({ ...DEFAULT_PLUGIN_PARAMS, ...(pluginParams ?? {}) });
    return { videoWidth: ctx.videoWidth, videoHeight: ctx.videoHeight };
  },
});
