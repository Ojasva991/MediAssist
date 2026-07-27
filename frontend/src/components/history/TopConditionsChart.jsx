const ROW_HEIGHT = 34;
const WIDTH = 640;
const PAD_LEFT = 8;
const PAD_RIGHT = 48;
const LABEL_WIDTH = 180;

/**
 * Horizontal bar chart of the most frequent `possible_conditions`
 * labels. Expects `items` from computeTopConditions(): [{label, count}].
 */
export function TopConditionsChart({ items }) {
  const height = items.length * ROW_HEIGHT + 8;
  const maxCount = Math.max(...items.map((i) => i.count), 1);
  const barAreaWidth = WIDTH - LABEL_WIDTH - PAD_LEFT - PAD_RIGHT;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${height}`}
      className="h-auto w-full"
      role="img"
      aria-label="Most common possible conditions"
    >
      {items.map((item, i) => {
        const y = i * ROW_HEIGHT + 4;
        const barWidth = (item.count / maxCount) * barAreaWidth;
        return (
          <g key={item.label}>
            <text
              x={PAD_LEFT + LABEL_WIDTH - 12}
              y={y + ROW_HEIGHT / 2}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize="12"
              fill="var(--color-ink-soft)"
              className="font-sans"
            >
              {item.label.length > 26 ? `${item.label.slice(0, 25)}…` : item.label}
            </text>
            <rect
              x={PAD_LEFT + LABEL_WIDTH}
              y={y + 4}
              width={Math.max(barWidth, 4)}
              height={ROW_HEIGHT - 12}
              rx="4"
              fill="var(--color-primary)"
              opacity={0.85 - i * 0.1}
            />
            <text
              x={PAD_LEFT + LABEL_WIDTH + Math.max(barWidth, 4) + 8}
              y={y + ROW_HEIGHT / 2}
              dominantBaseline="middle"
              fontSize="12"
              className="font-mono"
              fill="var(--color-ink-faint)"
            >
              {item.count}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
