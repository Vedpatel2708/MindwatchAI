'use client';
/**
 * frontend/components/RiskAlertPanel.tsx — MINDWATCH
 * Shows high/crisis risk alerts. Reuses AlertPanel structure.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from './WebSocketProvider';

const RISK_CONFIG: Record<string, { border: string; bg: string; badge: string; label: string }> = {
  crisis:   { border: 'border-l-red-500',    bg: 'bg-red-50',    badge: 'bg-red-100 text-red-700 border-red-200',    label: 'CRISIS' },
  high:     { border: 'border-l-orange-400', bg: 'bg-orange-50', badge: 'bg-orange-100 text-orange-700 border-orange-200', label: 'HIGH RISK' },
  moderate: { border: 'border-l-yellow-400', bg: 'bg-yellow-50', badge: 'bg-yellow-100 text-yellow-700 border-yellow-200', label: 'MODERATE' },
};

function timeAgo(ts: string) {
  const s = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (s < 10) return 'just now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

interface Alert { id: string; assessment_id: string; risk_level: string; crisis_score: number; created_at: string; }

export default function RiskAlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsub = subscribe('assessment.completed', (payload: unknown) => {
      const e = payload as { assessment_id: string; risk_level: string; timestamp: string };
      if (['crisis', 'high', 'moderate'].includes(e.risk_level)) {
        setAlerts(prev => [{
          id: `${e.assessment_id}-alert`,
          assessment_id: e.assessment_id,
          risk_level: e.risk_level,
          crisis_score: 0,
          created_at: e.timestamp,
        }, ...prev].slice(0, 20));
      }
    });
    return unsub;
  }, [subscribe]);

  const criticalCount = alerts.filter(a => ['crisis', 'high'].includes(a.risk_level)).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-bold text-teal-900 uppercase tracking-wider">Risk Alerts</h2>
        {criticalCount > 0 ? (
          <motion.span animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 2, repeat: Infinity }}
            className="flex items-center gap-1.5 bg-red-50 border border-red-200 text-red-600 text-xs px-2 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-ping" />
            {criticalCount} critical
          </motion.span>
        ) : (
          <span className="text-xs text-green-600 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
            ✓ All clear
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {alerts.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 3, repeat: Infinity }} className="text-4xl mb-3">🟢</motion.div>
            <p className="text-teal-600/60 text-sm">No risk alerts</p>
            <p className="text-teal-500/40 text-xs mt-1">High-risk assessments appear here</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {alerts.map(alert => {
            const cfg = RISK_CONFIG[alert.risk_level] ?? RISK_CONFIG.moderate;
            return (
              <motion.div key={alert.id} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <Link href={`/assessments/${alert.assessment_id}`}>
                  <div className={`rounded-xl border-l-4 border border-teal-100 px-3 py-3 ${cfg.border} ${cfg.bg} hover:shadow-md transition-all cursor-pointer`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded border ${cfg.badge}`}>{cfg.label}</span>
                      <span className="text-xs text-teal-600/60">{timeAgo(alert.created_at)}</span>
                    </div>
                    <p className="text-xs text-teal-700/70">View full clinical analysis →</p>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
