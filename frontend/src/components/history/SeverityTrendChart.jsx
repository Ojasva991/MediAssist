import { SEVERITY_ORDER } from "@/lib/insights";

const SEVERITY_COLORS = {
  LOW: "var(--color-success)",
  MODERATE: "var(--color-warning)",
  HIGH: "var(--color-danger)",
  EMERGENCY: "var(--color-danger-dark)",
};

const WIDTH = 640;
const HEIGHT = 200;
const PAD_LEFT = 72;
const PAD_RIGHT = 16;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;

function formatShortDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

/**
 * Plots severity (LOW..EMERGENCY, 0-3) across a user's analysis history
 * over time. Expects `data` from computeSeverityTrend() - oldest first.
 * Needs at least 2 points to draw a meaningful line; renders nothing
 * useful below that (the caller decides whether to show the chart at all).
 */
export function SeverityTrendChart({ data }) {
  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const maxScore = SEVERITY_ORDER.length - 1;

  const xFor = (i) =>
    data.length === 1 ? PAD_LEFT + plotWidth / 2 : PAD_LEFT + (i / (data.length - 1)) * plotWidth;
  const yFor = (score) => PAD_TOP + plotHeight - (score / maxScore) * plotHeight;

  const linePath = data
    .map((point, i) => `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(1)} ${yFor(point.score).toFixed(1)}`)
    .join(" ");

  // Show at most ~6 date labels along the x-axis so it stays legible
  // regardless of how many points there are.
  const labelStep = Math.max(1, Math.ceil(data.length / 6));

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="h-auto w-full"
      role="img"
      aria-label="Severity trend over time"
    >
      {/* Horizontal gridlines + severity labels */}
      {SEVERITY_ORDER.map((label, i) => {
        const y = yFor(i);
        return (
          <g key={label}>
            <line
              x1={PAD_LEFT}
              x2={WIDTH - PAD_RIGHT}
              y1={y}
              y2={y}
              stroke="var(--color-border)"
              strokeWidth="1"
            />
            <text
              x={PAD_LEFT - 10}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              className="font-mono"
              fontSize="10"
              fill="var(--color-ink-faint)"
            >
              {label[0]}
              {label.slice(1, 3).toLowerCase()}
            </text>
          </g>
        );
      })}

      {/* Trend line */}
      <path d={linePath} fill="none" stroke="var(--color-primary)" strokeWidth="2" />

      {/* Points, colored by severity */}
      {data.map((point, i) => (
        <circle
          key={point.id}
          cx={xFor(i)}
          cy={yFor(point.score)}
          r="4"
          fill={SEVERITY_COLORS[point.severity] ?? "var(--color-primary)"}
          stroke="var(--color-surface)"
          strokeWidth="1.5"
        >
          <title>
            {point.severity} · {formatShortDate(point.date)}
          </title>
        </circle>
      ))}

      {/* X-axis date labels */}
      {data.map((point, i) =>
        i % labelStep === 0 ? (
          <text
            key={`label-${point.id}`}
            x={xFor(i)}
            y={HEIGHT - 6}
            textAnchor="middle"
            className="font-mono"
            fontSize="10"
            fill="var(--color-ink-faint)"
          >
            {formatShortDate(point.date)}
          </text>
        ) : null
      )}
    </svg>
  );
}
