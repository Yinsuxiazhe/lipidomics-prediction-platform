const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};
const toInt = (value, fallback, min, max) =>
  Math.round(clamp(toNumber(value, fallback), min, max));
const toText = (value, fallback) => {
  if (typeof value !== "string") return fallback;
  const resolved = value.trim();
  return resolved.length > 0 ? resolved : fallback;
};

export const DEFAULT_LAYOUT = Object.freeze({
  videoWidth: 1280,
  videoHeight: 720,
});

export const DEFAULT_ANIMATION = Object.freeze({
  typingSpeed: 2,
  cursorBlinkRate: 1.5,
  durationSeconds: 10,
});

export const DEFAULT_COMMANDS = Object.freeze({
  command: "help me analyze this lipidomics dataset and build a prediction model",
  responseLines: [
    "I'll help you analyze the lipidomics dataset.",
    "Let me start by exploring the data structure...",
    "",
    "▸ Loading 281_merge_lipids_enroll.csv",
    "▸ Found 281 samples × 156 lipid features",
    "▸ Detected responder groups: R (n=142) / NR (n=139)",
    "",
    "Building prediction pipeline with strict nested CV...",
    "Training complete. Outer-test AUC: 0.52 ± 0.08",
  ],
});

export const DEFAULT_PLUGIN_PARAMS = Object.freeze({
  ...DEFAULT_LAYOUT,
  ...DEFAULT_ANIMATION,
  ...DEFAULT_COMMANDS,
});

export const PARAM_FIELDS = Object.freeze([
  { key: "command", label: "Command", control: "textarea", section: "content" },
  { key: "responseLines", label: "Response (JSON array)", control: "textarea", section: "content" },
  { key: "videoWidth", label: "Width", control: "select", section: "layout", options: [720, 1080, 1280, 1920] },
  { key: "videoHeight", label: "Height", control: "select", section: "layout", options: [480, 720, 1080, 1280] },
  { key: "durationSeconds", label: "Duration (s)", control: "number", section: "animation", min: 3, max: 30, step: 0.5 },
  { key: "typingSpeed", label: "Typing Speed", control: "range", section: "animation", min: 0.5, max: 5, step: 0.25 },
  { key: "cursorBlinkRate", label: "Cursor Blink", control: "range", section: "animation", min: 0.5, max: 3, step: 0.25 },
]);

export const normalizeParamValue = ({ key, rawValue, currentValue }) => {
  switch (key) {
    case "command":
      return toText(rawValue, DEFAULT_PLUGIN_PARAMS.command);
    case "videoWidth":
      return toInt(rawValue, DEFAULT_PLUGIN_PARAMS.videoWidth, 480, 1920);
    case "videoHeight":
      return toInt(rawValue, DEFAULT_PLUGIN_PARAMS.videoHeight, 480, 1280);
    case "durationSeconds":
      return clamp(toNumber(rawValue, DEFAULT_PLUGIN_PARAMS.durationSeconds), 3, 30);
    case "typingSpeed":
      return clamp(toNumber(rawValue, DEFAULT_PLUGIN_PARAMS.typingSpeed), 0.5, 5);
    case "cursorBlinkRate":
      return clamp(toNumber(rawValue, DEFAULT_PLUGIN_PARAMS.cursorBlinkRate), 0.5, 3);
    default:
      return currentValue ?? rawValue;
  }
};
