import React, { useEffect, useState } from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

const CURSOR_COLOR = "#d97706";
const PROMPT_ACCENT = "#c084fc";
const RESPONSE_ACCENT = "#34d399";

const TerminalWindow = ({ children, scale, fadeIn }) => (
  <div
    style={{
      width: 1060 * scale,
      height: 620 * scale,
      borderRadius: 16 * scale,
      backgroundColor: "hsl(222 47% 11%)",
      border: `1px solid hsl(215 28% 17%)`,
      boxShadow: `0 ${25 * scale}px ${60 * scale}px rgba(0,0,0,0.5), 0 ${2 * scale}px ${8 * scale}px rgba(0,0,0,0.3)`,
      overflow: "hidden",
      opacity: fadeIn,
      transform: `translateY(${interpolate(fadeIn, [0, 1], [20, 0])}px)`,
    }}
  >
    {/* Title bar */}
    <div
      style={{
        height: 44 * scale,
        backgroundColor: "hsl(222 47% 9%)",
        borderBottom: `1px solid hsl(215 28% 17%)`,
        display: "flex",
        alignItems: "center",
        paddingLeft: 18 * scale,
        gap: 8 * scale,
      }}
    >
      {/* Traffic lights */}
      {["#ef4444", "#eab308", "#22c55e"].map((c, i) => (
        <div
          key={i}
          style={{
            width: 12 * scale,
            height: 12 * scale,
            borderRadius: "50%",
            backgroundColor: c,
          }}
        />
      ))}
      {/* Title */}
      <div
        style={{
          flex: 1,
          textAlign: "center",
          color: "hsl(215 20% 55%)",
          fontSize: 13 * scale,
          fontFamily: "'JetBrains Mono Variable', monospace",
          paddingRight: 54 * scale,
          letterSpacing: "0.02em",
        }}
      >
        claude — ~/project
      </div>
    </div>
    {/* Terminal body */}
    <div
      style={{
        padding: `${20 * scale}px ${28 * scale}px`,
        height: 576 * scale,
        overflow: "hidden",
        fontFamily: "'JetBrains Mono Variable', monospace",
        fontSize: 15 * scale,
        lineHeight: 1.65,
        color: "hsl(210 40% 88%)",
      }}
    >
      {children}
    </div>
  </div>
);

const PromptLine = ({ text, visibleChars, scale, showCursor, cursorVisible }) => {
  const displayText = text.slice(0, visibleChars);

  return (
    <div style={{ display: "flex", alignItems: "flex-start", marginBottom: 6 * scale }}>
      <span style={{ color: PROMPT_ACCENT, marginRight: 10 * scale, fontWeight: 600 }}>
        &gt;
      </span>
      <span style={{ flex: 1, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
        {displayText}
        {showCursor && (
          <span
            style={{
              color: CURSOR_COLOR,
              fontWeight: 700,
              opacity: cursorVisible ? 1 : 0,
              transition: "opacity 0.08s",
            }}
          >
            ▌
          </span>
        )}
      </span>
    </div>
  );
};

const ResponseBlock = ({ lines, visibleChars, scale }) => {
  let remaining = visibleChars;
  const renderedLines = [];

  for (let i = 0; i < lines.length && remaining > 0; i++) {
    const line = lines[i];
    if (line === "") {
      if (remaining >= 1) {
        renderedLines.push(<div key={`blank-${i}`} style={{ height: 10 * scale }} />);
        remaining -= 1;
      }
      continue;
    }

    const lineChars = Math.min(line.length, remaining);
    const visible = line.slice(0, lineChars);
    remaining -= lineChars + 1;

    const isArrow = line.startsWith("▸");
    const isThinking = line.startsWith("...");

    renderedLines.push(
      <div key={`line-${i}`} style={{ marginBottom: 3 * scale, whiteSpace: "pre-wrap" }}>
        {isArrow ? (
          <>
            <span style={{ color: RESPONSE_ACCENT }}>▸ </span>
            <span style={{ color: "hsl(210 40% 82%)" }}>
              {visible.slice(line.startsWith("▸ ") ? 2 : 1)}
            </span>
          </>
        ) : isThinking ? (
          <span style={{ color: "hsl(215 20% 55%)" }}>{visible}</span>
        ) : (
          <span style={{ color: "hsl(210 28% 80%)" }}>{visible}</span>
        )}
      </div>
    );
  }

  return <div>{renderedLines}</div>;
};

export const ClaudeCodeTerminalScene = ({
  command,
  responseLines,
  typingSpeed,
  cursorBlinkRate,
  phases,
  frame,
  fps,
  layout,
  onAutoLayoutReady,
}) => {
  useEffect(() => { onAutoLayoutReady?.(); }, [onAutoLayoutReady]);

  const {
    fadeInEnd, typingStart, typingEnd, pauseEnd, responseStart, responseEnd,
  } = phases;

  const videoWidth = layout?.videoWidth ?? 1280;
  const videoHeight = layout?.videoHeight ?? 720;
  const scale = videoWidth / 1280;

  // Fade in
  const fadeIn = interpolate(frame, [0, fadeInEnd], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // Typing progress (chars revealed)
  const typingDuration = Math.max(1, typingEnd - typingStart);
  const charsTyped = frame < typingStart
    ? 0
    : frame >= typingEnd
      ? command.length
      : Math.floor(((frame - typingStart) / typingDuration) * command.length);

  // Cursor blink
  const blinkCycle = fps / cursorBlinkRate;
  const cursorVisible = Math.floor(frame / blinkCycle) % 2 === 0;

  // Response typing
  const responseLinesArr = Array.isArray(responseLines) ? responseLines : [];
  const totalResponseChars = responseLinesArr.reduce((s, l) => s + l.length + 1, 0);
  const responseDuration = Math.max(1, responseEnd - responseStart);
  const responseChars = frame < responseStart
    ? 0
    : frame >= responseEnd
      ? totalResponseChars
      : Math.floor(((frame - responseStart) / responseDuration) * totalResponseChars);

  // Show cursor during command typing and during response
  const showCursor = frame >= typingStart && frame < responseStart;

  // Spinning indicator during response
  const spinnerChars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
  const spinnerIdx = Math.floor(frame / 3) % spinnerChars.length;
  const isResponding = frame >= responseStart && frame < responseEnd;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "hsl(224 38% 8%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Subtle gradient bg */}
      <div
        style={{
          position: "absolute",
          width: "60%",
          aspectRatio: "1/1",
          left: "50%",
          top: "45%",
          transform: "translate(-50%, -50%)",
          filter: `blur(${120 * scale}px)`,
          background: "radial-gradient(circle, hsl(270 60% 40% / 0.15) 0%, hsl(240 50% 30% / 0.08) 50%, transparent 80%)",
        }}
      />

      <TerminalWindow scale={scale} fadeIn={fadeIn}>
        {/* Claude branding line */}
        <div
          style={{
            color: "hsl(215 20% 45%)",
            fontSize: 12 * scale,
            marginBottom: 14 * scale,
            display: "flex",
            alignItems: "center",
            gap: 8 * scale,
          }}
        >
          <span style={{ color: CURSOR_COLOR, fontSize: 16 * scale }}>✦</span>
          <span>Claude Code</span>
          <span style={{ color: "hsl(215 15% 30%)" }}>|</span>
          <span style={{ color: "hsl(215 15% 38%)" }}>~/project</span>
        </div>

        {/* Command prompt */}
        <PromptLine
          text={command}
          visibleChars={charsTyped}
          scale={scale}
          showCursor={showCursor}
          cursorVisible={cursorVisible}
        />

        {/* Response area */}
        {(frame >= responseStart) && (
          <>
            {isResponding && (
              <div style={{ marginBottom: 8 * scale, color: "hsl(215 20% 45%)", fontSize: 13 * scale }}>
                <span style={{ color: RESPONSE_ACCENT }}>{spinnerChars[spinnerIdx]}</span>
                {" "}Thinking...
              </div>
            )}
            <ResponseBlock
              lines={responseLinesArr}
              visibleChars={responseChars}
              scale={scale}
            />
          </>
        )}
      </TerminalWindow>
    </AbsoluteFill>
  );
};
