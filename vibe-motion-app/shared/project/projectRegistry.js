import { demoMotionPlugin } from "../features/demoMotion/plugins/demoMotionPlugin.js";
import { claudeCodeTerminalPlugin } from "../features/claudeCodeTerminal/plugins/claudeCodeTerminalPlugin.js";
import { mapCompositionsById, mapPluginsById } from "../scaffold/projectBindingRuntime.js";

export const PROJECT_PLUGINS = Object.freeze([demoMotionPlugin, claudeCodeTerminalPlugin]);
export const PROJECT_PLUGINS_BY_ID = mapPluginsById(PROJECT_PLUGINS);

export const PROJECT_COMPOSITIONS = Object.freeze([
  {
    id: "ScaffoldDemo30fps",
    fps: 30,
    pluginId: demoMotionPlugin.id,
  },
  {
    id: "ClaudeCodeTerminal30fps",
    fps: 30,
    pluginId: claudeCodeTerminalPlugin.id,
  },
]);
export const PROJECT_COMPOSITIONS_BY_ID = mapCompositionsById(PROJECT_COMPOSITIONS);
