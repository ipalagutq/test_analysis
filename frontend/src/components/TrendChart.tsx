"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Flag, Trend } from "@/lib/api";

// same colors as the .flag-* classes in globals.css
const FLAG_COLORS: Record<Flag, string> = {
  low: "#1d4ed8",
  normal: "#15803d",
  high: "#9b1c1c",
  unknown: "#5c6675",
};

interface DotProps {
  cx?: number;
  cy?: number;
  payload?: { flag: Flag };
}

/** Point colored by its flag, so out-of-range values stand out on the line. */
function FlagDot({ cx, cy, payload }: DotProps) {
  if (cx === undefined || cy === undefined || payload === undefined) {
    return null;
  }
  return <circle cx={cx} cy={cy} r={5} fill={FLAG_COLORS[payload.flag]} stroke="#ffffff" />;
}

/** Y domain that keeps both the points and the reference interval in view. */
function yDomain(trend: Trend): [number, number] {
  const values = trend.points.map((point) => point.value);
  for (const bound of [trend.ref_low, trend.ref_high]) {
    if (bound !== null) {
      values.push(bound);
    }
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min) * 0.1 || Math.abs(max) * 0.1 || 1;
  return [Math.max(0, min - padding), max + padding];
}

function formatNumber(value: number): string {
  return Number(value.toFixed(2)).toString();
}

function referenceLabel(trend: Trend): string {
  if (trend.ref_low !== null && trend.ref_high !== null) {
    return `${trend.ref_low}–${trend.ref_high} ${trend.unit}`;
  }
  if (trend.ref_low !== null) {
    return `≥ ${trend.ref_low} ${trend.unit}`;
  }
  if (trend.ref_high !== null) {
    return `≤ ${trend.ref_high} ${trend.unit}`;
  }
  return "нет в справочнике";
}

interface TrendChartProps {
  trend: Trend;
  title: string;
}

/** One test's values across visits with the reference interval as a shaded band. */
export default function TrendChart({ trend, title }: TrendChartProps) {
  if (trend.points.length === 0) {
    return <p className="muted">Нет значений для этого показателя.</p>;
  }

  const [domainLow, domainHigh] = yDomain(trend);
  const hasReference = trend.ref_low !== null || trend.ref_high !== null;

  return (
    <figure className="trend-chart">
      <figcaption>
        {title}, {trend.unit} · норма: {referenceLabel(trend)}
      </figcaption>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={trend.points} margin={{ top: 12, right: 24, bottom: 8, left: 8 }}>
          <CartesianGrid stroke="#e5e8ec" strokeDasharray="3 3" />
          {hasReference && (
            <ReferenceArea
              y1={trend.ref_low ?? domainLow}
              y2={trend.ref_high ?? domainHigh}
              fill="#15803d"
              fillOpacity={0.12}
              ifOverflow="extendDomain"
            />
          )}
          <XAxis dataKey="collected_at" tick={{ fontSize: 12 }} />
          <YAxis
            domain={[domainLow, domainHigh]}
            tickFormatter={formatNumber}
            tick={{ fontSize: 12 }}
            width={56}
          />
          <Tooltip
            formatter={(value: number) => [`${formatNumber(value)} ${trend.unit}`, title]}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#2563eb"
            strokeWidth={2}
            dot={<FlagDot />}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </figure>
  );
}
