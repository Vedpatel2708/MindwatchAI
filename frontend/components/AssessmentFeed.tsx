'use client';
/**
 * frontend/components/AssessmentFeed.tsx — MINDWATCH
 * Live feed of submitted assessments with risk level badges.
 * Reuses the same WebSocket + AnimatePresence pattern from TransactionFeed.
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from './WebSocketProvider';
import { fetchAssessments, type Assessment } from '@/lib/api';

const MAX_ITEMS = 30;

const RISK_CONFIG: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  safe:     { bg: 'bg-green-50',   text: 'text-green-700',  border: 'border-green-200',  icon: '🟢' },
  low:      { bg: 'bg-teal-50',    text: 'text-teal-700',   border: 'border-teal-200',   icon: '🔵' },
  moderate: { bg: 'bg-yellow-50',  text: 'text-yellow-700', border: 'border-yellow-200', icon: '🟡' },
  high:     { bg: 'bg-orange-50',  text: 'text-orange-700', border: 'border-orange-200', icon: '🟠' },
  crisis:   { bg: 'bg-red-50',     text: 'text-red-700',    border: 'border-red-200',    icon: '🔴' },
  analyzing:{ bg: 'bg-gray-50',    text: 'text-gray-600',   border: 'border-gray-200',   icon: '⏳' },
};

const EMOTION_ICONS: Record<string, string> = {
  sadness: '😔', hopelessness: '😞', fear: '😨', anger: '😠',
  numbness: '😶', loneliness: '🥺', shame: '😳', exhaustion: '😩', neutral: '😐',
};

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function AssessmentFeed() {
  const [items, setItems] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    fetchAssessments({ page: 1, page_size: 15 })
      .then(r => setItems(r.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const unsub1 = subscribe('assessment.submitted', (payload: unknown) => {
      const e = payload as { assessment_id: string; risk_level: string; crisis_score: number; dominant_emotion: string; timestamp: string };
      const item: Assessment = {
        id: e.assessment_id, input_text: '', input_type: 'journal',
        risk_level: e.risk_level, crisis_score: e.crisis_score,
        dominant_emotion: e.dominant_emotion, status: 'pending', submitted_at: e.timestamp,
      };
      setItems(prev => [item, ...prev].slice(0, MAX_ITEMS));
    });

    const unsub2 = subscribe('assessment.completed', (payload: unknown) => {
      const e = payload as { assessment_id: string; risk_level: string };
      setItems(prev => prev.map(a =>
        a.id === e.assessment_id ? { ...a, risk_level: e.risk_level, status: 'completed' } : a
      ));
    });

    return () => { unsub1(); unsub2(); };
  }, [subscribe]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-bold text-teal-900 uppercase tracking-wider">Live Assessments</h2>
        <span className="text-xs text-teal-600 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-full font-mono">
          {items.length}/{MAX_ITEMS}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {loading && [...Array(5)].map((_, i) => (
          <div key={i} className="h-14 rounded-xl bg-teal-50 border border-teal-100 animate-pulse" />
        ))}

        {!loading && items.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <motion.div animate={{ y: [0, -8, 0] }} transition={{ duration: 2, repeat: Infinity }} className="text-4xl mb-3 opacity-40">🧠</motion.div>
            <p className="text-teal-600/60 text-sm">Waiting for assessments...</p>
            <p className="text-teal-500/40 text-xs mt-1">Submit a journal entry to begin</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {items.map(item => {
            const cfg = RISK_CONFIG[item.risk_level] ?? RISK_CONFIG.analyzing;
            const emoIcon = EMOTION_ICONS[item.dominant_emotion ?? ''] ?? '😐';
            return (
              <motion.div key={item.id}
                initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className={`rounded-xl px-3 py-2.5 border ${cfg.bg} ${cfg.border}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="text-lg shrink-0">{emoIcon}</span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-teal-900 capitalize">{item.dominant_emotion ?? 'Analyzing...'}</p>
                      <p className="text-xs text-teal-600/60">{formatTime(item.submitted_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.crisis_score !== undefined && (
                      <span className="text-xs font-mono text-teal-700">{(item.crisis_score * 100).toFixed(0)}%</span>
                    )}
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border capitalize ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                      {item.risk_level}
                    </span>
                    {item.risk_level === 'crisis' && (
                      <motion.span animate={{ scale: [1, 1.3, 1] }} transition={{ duration: 1.2, repeat: Infinity }}
                        className="w-2 h-2 bg-red-500 rounded-full" />
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
