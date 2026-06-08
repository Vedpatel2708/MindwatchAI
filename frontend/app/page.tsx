'use client';
import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from '@/components/WebSocketProvider';
import { fetchAnalyticsSummary, submitAssessment, type AnalyticsSummary, type Assessment } from '@/lib/api';

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ icon, iconColor, value, label, pulse, suffix }: {
  icon: string; iconColor: string; value: string | number; label: string;
  pulse?: boolean; suffix?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      className="bg-surface-container rounded-xl border border-outline-variant p-4 flex flex-col justify-between shadow-sm">
      <div className="flex items-start justify-between">
        <span className={`material-symbols-outlined text-[20px] ${iconColor}`}>{icon}</span>
        {pulse && <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />}
      </div>
      <div className="mt-2">
        <p className="font-display text-3xl font-bold text-on-surface stat-number">
          {value}{suffix && <span className="text-xl font-medium">{suffix}</span>}
        </p>
        <p className="font-label-md text-on-surface-variant mt-1">{label}</p>
      </div>
    </motion.div>
  );
}

// ── Assessment Feed Item ────────────────────────────────────────────────────────
const RISK_COLORS: Record<string, { dot: string; badge: string; text: string }> = {
  crisis:   { dot: 'bg-error', badge: 'bg-error-container text-on-error-container', text: 'text-error' },
  high:     { dot: 'bg-error', badge: 'bg-error-container/50 text-error', text: 'text-error' },
  moderate: { dot: 'bg-secondary', badge: 'bg-secondary-container text-on-secondary-container', text: 'text-secondary' },
  low:      { dot: 'bg-tertiary', badge: 'bg-tertiary-container text-on-tertiary-container', text: 'text-tertiary' },
  safe:     { dot: 'bg-primary', badge: 'bg-primary-container text-on-primary-container', text: 'text-primary' },
};

function AssessmentItem({ item, index }: { item: Assessment; index: number }) {
  const cfg = RISK_COLORS[item.risk_level] ?? RISK_COLORS.safe;
  const emotion = item.dominant_emotion ?? 'analyzing';
  const score = item.crisis_score !== undefined ? `${(item.crisis_score * 100).toFixed(0)}%` : '—';

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center justify-between py-3 border-b border-outline-variant last:border-0 group hover:bg-surface-container-high rounded-lg px-2 transition-colors cursor-pointer">
      <div className="flex items-center gap-3">
        <div className={`h-2 w-2 rounded-full ${cfg.dot} flex-shrink-0`} />
        <div>
          <p className="font-label-md text-on-surface capitalize">{emotion}</p>
          <p className="font-body-md text-xs text-on-surface-variant">
            {new Date(item.submitted_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-label-md text-sm text-on-surface-variant">{score}</span>
        <span className={`font-label-md text-xs px-2 py-0.5 rounded-full capitalize ${cfg.badge}`}>
          {item.risk_level}
        </span>
      </div>
    </motion.div>
  );
}

// ── Inline Analysis Form ────────────────────────────────────────────────────────
function InlineAnalyzer() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (text.trim().length < 10) { setError('Please enter at least 10 characters.'); return; }
    setLoading(true); setError('');
    try {
      const result = await submitAssessment({ input_text: text, input_type: 'journal' });
      const assessmentId = result.assessment_id;
      if (!assessmentId) throw new Error('No assessment ID returned');
      router.push(`/assessments/${assessmentId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed. Is the backend running?');
      setLoading(false);
    }
  };

  return (
    <div className="mt-4">
      <textarea
        value={text}
        onChange={e => { setText(e.target.value); setError(''); }}
        placeholder="Paste a journal entry, message, or clinical note here..."
        rows={4}
        className="w-full bg-surface-container-high border border-outline-variant rounded-xl px-4 py-3 text-on-surface placeholder-on-surface-variant/50 text-sm resize-none focus:outline-none focus:border-primary transition-colors"
      />
      {error && <p className="text-error text-xs mt-1">{error}</p>}
      <div className="flex items-center justify-between mt-3">
        <p className="text-xs text-on-surface-variant">{text.length} characters</p>
        <button
          onClick={handleSubmit}
          disabled={loading || text.length < 10}
          className="bg-primary text-on-primary hover:bg-primary-fixed font-label-md px-6 py-2 rounded-full flex items-center gap-2 font-semibold glow-btn transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
          <span className="material-symbols-outlined text-[18px]">
            {loading ? 'hourglass_empty' : 'document_scanner'}
          </span>
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [recentAssessments, setRecentAssessments] = useState<Assessment[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<Assessment[]>([]);
  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    fetchAnalyticsSummary().then(setAnalytics).catch(() => {});

    // Fetch recent assessments
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/assessments?page_size=8`)
      .then(r => r.json()).then(j => {
        if (j.data?.items) {
          setRecentAssessments(j.data.items);
          setRiskAlerts(j.data.items.filter((a: Assessment) => ['crisis', 'high'].includes(a.risk_level)));
        }
      }).catch(() => {});

    const t = setInterval(() => {
      fetchAnalyticsSummary().then(setAnalytics).catch(() => {});
    }, 60000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const u1 = subscribe('assessment.submitted', (payload: unknown) => {
      const e = payload as { assessment_id: string; risk_level: string; crisis_score: number; dominant_emotion: string; timestamp: string };
      const item: Assessment = {
        id: e.assessment_id,
        input_text: '',
        input_type: 'journal',
        risk_level: e.risk_level,
        crisis_score: e.crisis_score,
        dominant_emotion: e.dominant_emotion,
        status: 'pending',
        submitted_at: e.timestamp,
      };
      setRecentAssessments(prev => [item, ...prev].slice(0, 8));
    });
    const u2 = subscribe('assessment.completed', (payload: unknown) => {
      const e = payload as { assessment_id: string; risk_level: string };
      setRecentAssessments(prev =>
        prev.map(a => a.id === e.assessment_id ? { ...a, risk_level: e.risk_level, status: 'completed' } : a)
      );
      if (['crisis', 'high'].includes(e.risk_level)) {
        setRiskAlerts(prev => [{ id: e.assessment_id, risk_level: e.risk_level } as Assessment, ...prev].slice(0, 5));
      }
    });
    return () => { u1(); u2(); };
  }, [subscribe]);

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 space-y-6 mt-4">
      {/* Dashboard Header */}
      <div>
        <h1 className="font-display text-2xl md:text-3xl font-semibold text-on-surface">System Overview</h1>
        <p className="font-body-md text-on-surface-variant mt-1">Real-time clinical intelligence monitoring.</p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6">

        {/* LEFT COLUMN */}
        <div className="md:col-span-8 space-y-4 md:space-y-6">

          {/* Primary Action Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="bg-surface-container border border-outline-variant rounded-xl p-6 relative overflow-hidden border-l-4 border-l-primary glow-effect shadow-sm">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-primary text-[32px]">psychology</span>
                <h2 className="font-title-lg text-on-surface">Analyze Mental Health Text</h2>
              </div>
              <p className="font-body-md text-on-surface-variant mb-4 max-w-2xl">
                Deploy multi-modal clinical screening on patient narratives, session transcripts, or messages.
                Detect risk markers, cognitive distortions, and sentiment escalation using BioBERT embeddings + 3 trained ML classifiers.
              </p>

              <AnimatePresence mode="wait">
                {showAnalyzer ? (
                  <motion.div key="analyzer" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                    <InlineAnalyzer />
                    <button onClick={() => setShowAnalyzer(false)} className="mt-2 text-xs text-on-surface-variant hover:text-primary transition-colors">
                      ← Collapse
                    </button>
                  </motion.div>
                ) : (
                  <motion.div key="buttons" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-wrap gap-3">
                    <button
                      onClick={() => setShowAnalyzer(true)}
                      className="bg-primary text-on-primary hover:bg-primary-fixed font-label-md px-6 py-2 rounded-full flex items-center gap-2 font-semibold glow-btn transition-colors">
                      <span className="material-symbols-outlined text-[18px]">document_scanner</span>
                      Initiate Text Analysis
                    </button>
                    <Link href="/chat"
                      className="border border-primary text-primary hover:bg-primary-container font-label-md px-6 py-2 rounded-full flex items-center gap-2 font-semibold transition-colors">
                      <span className="material-symbols-outlined text-[18px]">forum</span>
                      Open Support Chat
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Live Assessments + Risk Alerts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Live Assessments */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="bg-surface-container rounded-xl border border-outline-variant p-4 flex flex-col shadow-sm min-h-[280px]">
              <div className="flex items-center justify-between mb-3 border-b border-outline-variant pb-2">
                <h3 className="font-label-md text-on-surface uppercase tracking-wider">Live Assessments</h3>
                <span className="material-symbols-outlined text-on-surface-variant text-[18px]">sensors</span>
              </div>
              {recentAssessments.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center py-8 opacity-70">
                  <span className="material-symbols-outlined text-outline text-[48px] mb-2">clinical_notes</span>
                  <p className="font-body-md text-on-surface font-medium">No Active Sessions</p>
                  <p className="font-body-md text-on-surface-variant text-center mt-1 text-sm">
                    Awaiting incoming telemetry or session initialization.
                  </p>
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto">
                  {recentAssessments.map((item, i) => (
                    <Link key={item.id} href={`/assessments/${item.id}`}>
                      <AssessmentItem item={item} index={i} />
                    </Link>
                  ))}
                </div>
              )}
            </motion.div>

            {/* Risk Alerts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
              className="bg-surface-container rounded-xl border border-outline-variant p-4 flex flex-col shadow-sm min-h-[280px]">
              <div className="flex items-center justify-between mb-3 border-b border-outline-variant pb-2">
                <h3 className="font-label-md text-on-surface uppercase tracking-wider">Risk Alerts</h3>
                <span className="material-symbols-outlined text-on-surface-variant text-[18px]">warning</span>
              </div>
              {riskAlerts.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center py-8">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-2 border border-primary/20 card-glow">
                    <span className="material-symbols-outlined text-primary text-[32px]">check_circle</span>
                  </div>
                  <p className="font-body-md text-primary font-medium">All Clear</p>
                  <p className="font-body-md text-on-surface-variant text-center mt-1 text-sm">
                    No elevated risk patterns detected.
                  </p>
                </div>
              ) : (
                <div className="flex-1 space-y-2 overflow-y-auto">
                  {riskAlerts.map((alert, i) => (
                    <Link key={alert.id} href={`/assessments/${alert.id}`}>
                      <motion.div
                        initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                        className="flex items-center justify-between p-3 bg-error-container/20 border border-error/30 rounded-xl hover:bg-error-container/30 transition-colors cursor-pointer">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-error text-[20px]">warning</span>
                          <div>
                            <p className="font-label-md text-on-surface capitalize">{alert.risk_level} risk</p>
                            <p className="text-xs text-on-surface-variant">{new Date(alert.submitted_at || '').toLocaleTimeString()}</p>
                          </div>
                        </div>
                        <span className="material-symbols-outlined text-on-surface-variant text-[16px]">chevron_right</span>
                      </motion.div>
                    </Link>
                  ))}
                </div>
              )}
            </motion.div>
          </div>

          {/* Quick Actions Row */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { href: '/analyze', icon: 'psychology', label: 'Deep Analysis', desc: 'Full clinical screening' },
              { href: '/chat', icon: 'forum', label: 'Support Chat', desc: 'AI-powered guidance' },
              { href: '/analytics', icon: 'analytics', label: 'Insights', desc: '7-day trend report' },
            ].map((item, i) => (
              <Link key={item.href} href={item.href}>
                <motion.div
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.05 }}
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="bg-surface-container border border-outline-variant rounded-xl p-4 cursor-pointer hover:border-primary/50 hover:glow-effect transition-all">
                  <span className="material-symbols-outlined text-primary text-[24px] mb-2 block">{item.icon}</span>
                  <p className="font-label-md text-on-surface text-sm">{item.label}</p>
                  <p className="text-xs text-on-surface-variant mt-0.5">{item.desc}</p>
                </motion.div>
              </Link>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN — Stats */}
        <div className="md:col-span-4">
          <div className="grid grid-cols-2 md:grid-cols-1 gap-3 md:gap-4">
            <StatCard
              icon="monitor_heart"
              iconColor="text-on-surface-variant"
              value={analytics?.total_assessments_today ?? 0}
              label="Assessments Today"
              pulse
            />
            <StatCard
              icon="warning"
              iconColor="text-error"
              value={analytics?.high_risk_today ?? 0}
              label="High Risk Today"
            />
            <StatCard
              icon="notifications"
              iconColor="text-tertiary"
              value={analytics?.open_alerts ?? 0}
              label="Open Alerts"
            />
            <StatCard
              icon="trending_up"
              iconColor="text-primary"
              value={(analytics ? (analytics.crisis_rate_today * 100).toFixed(1) : '0.0')}
              label="Crisis Rate"
              suffix="%"
            />
          </div>

          {/* Emotion breakdown card */}
          {analytics && Object.keys(analytics.emotion_distribution).length > 0 && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
              className="mt-4 bg-surface-container rounded-xl border border-outline-variant p-4 shadow-sm">
              <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3">Emotion Signals</h3>
              <div className="space-y-2">
                {Object.entries(analytics.emotion_distribution)
                  .sort((a, b) => b[1] - a[1]).slice(0, 4)
                  .map(([emotion, count]) => {
                    const max = Math.max(...Object.values(analytics.emotion_distribution));
                    const pct = Math.round((count / max) * 100);
                    return (
                      <div key={emotion}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-label-md text-on-surface-variant text-xs capitalize">{emotion}</span>
                          <span className="font-label-md text-on-surface text-xs">{count}</span>
                        </div>
                        <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-primary rounded-full"
                            initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, delay: 0.5 }} />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </motion.div>
          )}

          {/* Crisis Resources */}
          <div className="mt-4 bg-error-container/20 border border-error/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-error text-[18px]">emergency</span>
              <h3 className="font-label-md text-error uppercase tracking-wider text-xs">Crisis Resources</h3>
            </div>
            <div className="space-y-1 text-xs text-on-surface-variant">
              <p>📞 <strong className="text-on-surface">988</strong> — Suicide & Crisis Lifeline</p>
              <p>💬 Text <strong className="text-on-surface">HOME</strong> to 741741</p>
              <p>🆘 Emergency: <strong className="text-on-surface">911</strong></p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
