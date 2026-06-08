'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { fetchAnalyticsSummary, type AnalyticsSummary } from '@/lib/api';
import AnalyticsChart from '@/components/AnalyticsChart';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsSummary().then(setAnalytics).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 mt-4 space-y-6">
      <div>
        <h1 className="font-display text-2xl md:text-3xl font-semibold text-on-surface">Analytics</h1>
        <p className="font-body-md text-on-surface-variant mt-1">Clinical intelligence trends and population-level insights.</p>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
            <span className="material-symbols-outlined text-primary text-[40px]">progress_activity</span>
          </motion.div>
        </div>
      )}

      {!loading && analytics && (
        <>
          {/* Stat Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
            {[
              { icon: 'monitor_heart', color: 'text-on-surface-variant', label: 'Assessments Today', value: analytics.total_assessments_today.toString(), pulse: true },
              { icon: 'warning', color: 'text-error', label: 'High Risk Today', value: analytics.high_risk_today.toString() },
              { icon: 'notifications', color: 'text-tertiary', label: 'Open Alerts', value: analytics.open_alerts.toString() },
              { icon: 'trending_up', color: 'text-primary', label: 'Crisis Rate', value: `${(analytics.crisis_rate_today * 100).toFixed(1)}%` },
            ].map((s, i) => (
              <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                className="bg-surface-container rounded-xl border border-outline-variant p-4 shadow-sm">
                <div className="flex items-start justify-between">
                  <span className={`material-symbols-outlined text-[20px] ${s.color}`}>{s.icon}</span>
                  {s.pulse && <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />}
                </div>
                <p className="font-display text-3xl font-bold text-on-surface mt-2 stat-number">{s.value}</p>
                <p className="font-label-md text-on-surface-variant mt-1 text-xs">{s.label}</p>
              </motion.div>
            ))}
          </div>

          {/* Chart */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="bg-surface-container rounded-xl border border-outline-variant p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary text-[20px]">show_chart</span>
              <h2 className="font-label-md text-on-surface uppercase tracking-wider text-sm">7-Day Assessment Trend</h2>
            </div>
            <AnalyticsChart dailySeries={analytics.daily_series} />
          </motion.div>

          {/* Emotion Distribution */}
          {Object.keys(analytics.emotion_distribution).length > 0 && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
              className="bg-surface-container rounded-xl border border-outline-variant p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary text-[20px]">sentiment_very_dissatisfied</span>
                <h2 className="font-label-md text-on-surface uppercase tracking-wider text-sm">Emotion Distribution (7 days)</h2>
              </div>
              <div className="space-y-3">
                {Object.entries(analytics.emotion_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .map(([emotion, count], i) => {
                    const max = Math.max(...Object.values(analytics.emotion_distribution));
                    const pct = Math.round((count / max) * 100);
                    return (
                      <div key={emotion}>
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-label-md text-on-surface-variant text-xs capitalize">{emotion}</p>
                          <p className="font-label-md text-on-surface text-xs">{count}</p>
                        </div>
                        <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <motion.div className="h-full bg-primary rounded-full"
                            initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                            transition={{ delay: i * 0.08 + 0.5, duration: 0.8 }} />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </motion.div>
          )}
        </>
      )}
    </main>
  );
}
