'use client';
/**
 * frontend/components/AnalyticsChart.tsx — MINDWATCH
 * 7-day assessments vs high-risk trend chart.
 * Teal/sage color scheme.
 */

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import type { DailyDataPoint } from '@/lib/api';

interface Props { dailySeries: DailyDataPoint[]; }

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-container-high border border-outline-variant rounded-xl p-3 shadow-lg">
      <p className="text-xs text-on-surface-variant mb-2 font-label-md">{label}</p>
      {payload.map(e => (
        <p key={e.name} className="text-sm font-semibold" style={{ color: e.color }}>
          {e.name}: <span className="font-mono">{e.value}</span>
        </p>
      ))}
    </div>
  );
}

export default function AnalyticsChart({ dailySeries }: Props) {
  const data = dailySeries.map(d => ({
    ...d,
    displayDate: new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  if (!data.length) return (
    <div className="flex items-center justify-center h-48 text-teal-600/40 text-sm">No data yet</div>
  );

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(78,70,57,0.5)" vertical={false} />
        <XAxis dataKey="displayDate" tick={{ fill: '#d1c5b4', fontSize: 11 }} axisLine={{ stroke: '#4e4639' }} tickLine={false} />
        <YAxis tick={{ fill: '#d1c5b4', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '12px', color: '#d1c5b4' }} iconType="circle" iconSize={8} />
        <Line type="monotone" dataKey="assessments" name="Assessments" stroke="#f5bc4e" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
        <Line type="monotone" dataKey="high_risk" name="High Risk" stroke="#ffb4ab" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
