import { DEFAULT_PLUGIN_PARAMS } from "../config/claudeCodeTerminalDefaults.js";

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};
const toInt = (value, fallback, min, max) =>
  Math.round(clamp(toNumber(value, fallback), min, max));
const toPositiveFrames = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(1, Math.round(parsed)) : fallback;
};
const toFrame = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(0, Math.floor(parsed)) : fallback;
};

export const resolveSceneContext = (pluginParams = {}) => ({
  videoWidth: toInt(pluginParams.videoWidth, DEFAULT_PLUGIN_PARAMS.videoWidth, 480, 1920),
  videoHeight: toInt(pluginParams.videoHeight, DEFAULT_PLUGIN_PARAMS.videoHeight, 480, 1280),
  typingSpeed: clamp(toNumber(pluginParams.typingSpeed, DEFAULT_PLUGIN_PARAMS.typingSpeed), 0.5, 5),
  cursorBlinkRate: clamp(toNumber(pluginParams.cursorBlinkRate, DEFAULT_PLUGIN_PARAMS.cursorBlinkRate), 0.5, 3),
  durationSeconds: clamp(toNumber(pluginParams.durationSeconds, DEFAULT_PLUGIN_PARAMS.durationSeconds), 3, 30),
  command: pluginParams.command || DEFAULT_PLUGIN_PARAMS.command,
  responseLines: pluginParams.responseLines || DEFAULT_PLUGIN_PARAMS.responseLines,
});

export const getDurationInFrames = ({ fps, sceneContext }) => {
  const resolvedFps = toPositiveFrames(fps, 30);
  return toPositiveFrames(sceneContext.durationSeconds * resolvedFps, resolvedFps);
};

export const buildSceneProps = ({ frame = 0, fps, sceneContext }) => {
  const durationInFrames = getDurationInFrames({ fps, sceneContext });
  const rawFrame = toFrame(frame, 0);
  const boundedFrame = Math.min(rawFrame, durationInFrames - 1);
  const progress = durationInFrames <= 1 ? 0 : boundedFrame / (durationInFrames - 1);

  const fps30 = toPositiveFrames(fps, 30);

  // Phase timing (at 30fps)
  const fadeInEnd = Math.round(fps30 * 0.5);
  const typingStart = fadeInEnd;
  const commandChars = sceneContext.command.length;
  const typingEnd = typingStart + Math.round(commandChars / sceneContext.typingSpeed);
  const pauseEnd = typingEnd + Math.round(fps30 * 0.6);
  const responseStart = pauseEnd;
  const responseLines = sceneContext.responseLines;
  const totalResponseChars = responseLines.reduce((sum, l) => sum + l.length + 1, 0);
  const responseEnd = responseStart + Math.round(totalResponseChars / (sceneContext.typingSpeed * 4));

  return {
    ...sceneContext,
    durationInFrames,
    frame: boundedFrame,
    progress,
    fps: fps30,
    phases: {
      fadeInEnd,
      typingStart,
      typingEnd,
      pauseEnd,
      responseStart,
      responseEnd,
    },
  };
};
