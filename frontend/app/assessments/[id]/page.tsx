'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchAssessment, type Assessment, type AnalysisStep } from '@/lib/api';

const RISK_CONFIG: Record<string, { icon: string; color: string; bgColor: string; borderColor: string; label: string }> = {
  safe:     { icon: 'check_circle', color: 'text-primary', bgColor: 'bg-primary-container', borderColor: 'border-primary/30', label: 'Safe' },
  low:      { icon: 'info', color: 'text-tertiary', bgColor: 'bg-tertiary-container', borderColor: 'border-tertiary/30', label: 'Low Risk' },
  moderate: { icon: 'warning', color: 'text-secondary', bgColor: 'bg-secondary-container', borderColor: 'border-secondary/30', label: 'Moderate' },
  high:     { icon: 'error', color: 'text-error', bgColor: 'bg-error-container', borderColor: 'border-error/30', label: 'High Risk' },
  crisis:   { icon: 'emergency', color: 'text-error', bgColor: 'bg-error-container', borderColor: 'border-error/50', label: 'CRISIS' },
};

const STEP_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  thought:      { icon: 'psychology', color: 'text-primary', label: 'Reasoning' },
  action:       { icon: 'build', color: 'text-tertiary', label: 'Tool Call' },
  observation:  { icon: 'visibility', color: 'text-secondary', label: 'Observation' },
  final_answer: { icon: 'check_circle', color: 'text-primary', label: 'Conclusion' },
};

function StepCard({ step, index }: { step: AnalysisStep; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STEP_CONFIG[step.step_type] ?? { icon: 'circle', color: 'text-on-surface-variant', label: step.step_type };
  const hasDetail = !!(step.tool_input || step.tool_output);

  return (
    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.04 }}
      className={`rounded-xl border p-3 ${step.is_error ? 'bg-error-container/20 border-error/30' : 'bg-surface-container-high border-outline-variant'}`}>
      <div className="flex items-center gap-2">
        <span className={`material-symbols-outlined text-[18px] ${cfg.color}`}>{cfg.icon}</span>
        <span className="font-label-md text-xs text-on-surface-variant uppercase tracking-wider">{cfg.label}</span>
        {step.tool_name && (
          <code className="text-xs text-primary bg-primary-container px-2 py-0.5 rounded-full font-mono">{step.tool_name}</code>
        )}
        {hasDetail && (
          <button onClick={() => setExpanded(e => !e)} className="ml-auto text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[16px]">{expanded ? 'expand_less' : 'expand_more'}</span>
          </button>
        )}
        {step.is_error && <span className="ml-auto text-xs text-error flex items-center gap-0.5"><span className="material-symbols-outlined text-[14px]">error</span>Error</span>}
      </div>
      {step.content && (
        <p className="mt-2 text-sm text-on-surface leading-relaxed pl-7">{step.content}</p>
      )}
      {expanded && hasDetail && (
        <div className="mt-2 pl-7 space-y-2">
          {step.tool_input && (
            <div>
              <p className="text-xs text-on-surface-variant mb-1 font-label-md">Input:</p>
              <pre className="text-xs text-on-surface bg-surface-container rounded-lg p-3 overflow-x-auto">{JSON.stringify(step.tool_input, null, 2)}</pre>
            </div>
          )}
          {step.tool_output && (
            <div>
              <p className="text-xs text-on-surface-variant mb-1 font-label-md">Output:</p>
              <pre className="text-xs text-on-surface bg-surface-container rounded-lg p-3 overflow-x-auto max-h-40">{JSON.stringify(step.tool_output, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}

export default function AssessmentDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [polling, setPolling] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchAssessment(id);
      setAssessment(data);
      setPolling(data.status === 'pending' || data.status === 'analyzing');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Not found');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id && id !== 'undefined') load();
    else if (!id || id === 'undefined') {
      setError('Invalid assessment ID');
      setLoading(false);
    }
  }, [id, load]);
  useEffect(() => {
    if (!polling) return;
    // Poll every 2s while analyzing — agent steps appear in real time
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [polling, load]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
        <span className="material-symbols-outlined text-primary text-[48px]">progress_activity</span>
      </motion.div>
    </div>
  );

  if (error || !assessment) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="bg-surface-container rounded-xl border border-outline-variant p-8 text-center">
        <span className="material-symbols-outlined text-error text-[40px] mb-3 block">error</span>
        <p className="text-on-surface font-body-md">{error || 'Assessment not found'}</p>
        <Link href="/" className="text-primary hover:underline text-sm mt-4 block">← Back to Dashboard</Link>
      </div>
    </div>
  );

  const riskCfg = RISK_CONFIG[assessment.risk_level] ?? RISK_CONFIG.moderate;
  const steps = assessment.analysis_steps ?? [];
  const mlData = assessment as Record<string, unknown>;

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 mt-4 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-on-surface-variant">
        <Link href="/" className="hover:text-primary transition-colors">Dashboard</Link>
        <span className="material-symbols-outlined text-[14px]">chevron_right</span>
        <span className="text-on-surface">Assessment Report</span>
        {polling && (
          <span className="flex items-center gap-1 text-primary ml-auto text-xs">
            <span className="material-symbols-outlined text-[14px] animate-spin">progress_activity</span>
            Agent analyzing...
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left — Main Report */}
        <div className="md:col-span-8 space-y-4">

          {/* Risk Verdict Card */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className={`bg-surface-container rounded-xl border ${riskCfg.borderColor} p-6 relative overflow-hidden glow-effect shadow-sm`}>
            <div className={`absolute top-0 left-0 bottom-0 w-1.5 ${riskCfg.bgColor}`} />
            <div className="pl-4">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-12 h-12 rounded-full ${riskCfg.bgColor} flex items-center justify-center`}>
                  <span className={`material-symbols-outlined text-[28px] ${riskCfg.color}`}
                    style={{ fontVariationSettings: "'FILL' 1" }}>{riskCfg.icon}</span>
                </div>
                <div>
                  <p className={`font-display text-2xl font-bold ${riskCfg.color}`}>{riskCfg.label}</p>
                  <p className="text-on-surface-variant text-sm capitalize">{assessment.dominant_emotion} · {assessment.input_type}</p>
                </div>
                <div className="ml-auto text-right">
                  <p className="text-xs text-on-surface-variant">Crisis Score</p>
                  <p className={`font-display text-3xl font-bold ${riskCfg.color}`}>
                    {assessment.crisis_score !== undefined ? `${(assessment.crisis_score * 100).toFixed(0)}%` : '—'}
                  </p>
                </div>
              </div>

              {/* Score Bars */}
              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-outline-variant">
                {[
                  { label: 'Depression', value: assessment.depression_score, color: 'bg-secondary' },
                  { label: 'Anxiety', value: assessment.anxiety_score, color: 'bg-tertiary' },
                  { label: 'Crisis Signal', value: assessment.crisis_signal, color: 'bg-error' },
                ].map(s => (
                  <div key={s.label}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-label-md text-on-surface-variant text-xs">{s.label}</p>
                      <p className="font-label-md text-on-surface text-xs">
                        {s.value !== undefined ? `${(s.value * 100).toFixed(0)}%` : '—'}
                      </p>
                    </div>
                    <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                      <motion.div className={`h-full ${s.color} rounded-full`}
                        initial={{ width: 0 }} animate={{ width: `${(s.value || 0) * 100}%` }}
                        transition={{ delay: 0.3, duration: 0.8 }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* ML Model Outputs */}
              {(mlData.phq9_severity || mlData.crisis_ml_probability !== undefined) && (
                <div className="mt-4 pt-4 border-t border-outline-variant">
                  <p className="font-label-md text-on-surface-variant text-xs uppercase tracking-wider mb-3">ML Model Predictions</p>
                  <div className="grid grid-cols-3 gap-3">
                    {mlData.phq9_severity && String(mlData.phq9_severity) !== 'unknown' && (
                      <div className="bg-surface-container-highest rounded-xl p-3 text-center">
                        <span className="material-symbols-outlined text-secondary text-[20px] block mb-1">psychology_alt</span>
                        <p className="font-label-md text-on-surface text-xs capitalize">{String(mlData.phq9_severity).replace('_', ' ')}</p>
                        <p className="text-[10px] text-on-surface-variant">PHQ-9</p>
                      </div>
                    )}
                    {mlData.crisis_ml_probability !== undefined && Number(mlData.crisis_ml_probability) > 0 && (
                      <div className="bg-surface-container-highest rounded-xl p-3 text-center">
                        <span className="material-symbols-outlined text-error text-[20px] block mb-1">warning</span>
                        <p className="font-label-md text-on-surface text-xs">{(Number(mlData.crisis_ml_probability) * 100).toFixed(0)}%</p>
                        <p className="text-[10px] text-on-surface-variant">Crisis Prob.</p>
                      </div>
                    )}
                    {mlData.emotion_ml && String(mlData.emotion_ml) !== 'unknown' && (
                      <div className="bg-surface-container-highest rounded-xl p-3 text-center">
                        <span className="material-symbols-outlined text-tertiary text-[20px] block mb-1">sentiment_very_dissatisfied</span>
                        <p className="font-label-md text-on-surface text-xs capitalize">{String(mlData.emotion_ml)}</p>
                        <p className="text-[10px] text-on-surface-variant">Emotion ML</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {assessment.agent_summary && (
                <p className="mt-4 pt-4 border-t border-outline-variant text-sm text-on-surface leading-relaxed">
                  {assessment.agent_summary}
                </p>
              )}
            </div>
          </motion.div>

          {/* Recommendations */}
          {(assessment.recommendations?.length || assessment.resources?.length) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {assessment.recommendations?.length ? (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                  className="bg-surface-container rounded-xl border border-outline-variant p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="material-symbols-outlined text-primary text-[18px]">checklist</span>
                    <h3 className="font-label-md text-on-surface uppercase tracking-wider text-xs">Immediate Actions</h3>
                  </div>
                  <div className="space-y-2">
                    {assessment.recommendations.map((r, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-5 h-5 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-[10px] text-primary font-bold">{i + 1}</span>
                        </div>
                        <p className="text-sm text-on-surface">{r}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ) : null}
              {assessment.resources?.length ? (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
                  className="bg-surface-container rounded-xl border border-outline-variant p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="material-symbols-outlined text-tertiary text-[18px]">support</span>
                    <h3 className="font-label-md text-on-surface uppercase tracking-wider text-xs">Support Resources</h3>
                  </div>
                  <div className="space-y-2">
                    {assessment.resources.map((r, i) => (
                      <div key={i} className={`rounded-lg px-3 py-2 ${r.type === 'crisis' ? 'bg-error-container/20 border border-error/30' : 'bg-surface-container-high border border-outline-variant'}`}>
                        <p className="text-sm font-medium text-on-surface">{r.name}</p>
                        <p className="text-xs text-on-surface-variant">{r.contact}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ) : null}
            </div>
          ) : null}

          {/* Reasoning Trace */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[18px]">account_tree</span>
                <h3 className="font-label-md text-on-surface uppercase tracking-wider text-xs">Agent Reasoning Trace</h3>
              </div>
              <span className="text-xs text-on-surface-variant">{steps.length} steps</span>
            </div>

            {steps.length === 0 && polling ? (
              <div className="text-center py-10">
                <motion.div className="inline-block mb-3" animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 2, repeat: Infinity }}>
                  <span className="material-symbols-outlined text-primary text-[48px]">psychology</span>
                </motion.div>
                <p className="text-on-surface font-body-md font-medium">Agent Investigating...</p>
                <p className="text-on-surface-variant text-sm mt-1">Analyzing symptom patterns and building clinical assessment.</p>
                <div className="flex justify-center gap-1 mt-4">
                  {[0,1,2].map(i => (
                    <motion.div key={i} className="w-2 h-2 bg-primary rounded-full"
                      animate={{ y: [0, -6, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.2 }} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {steps.map((step, i) => <StepCard key={`${step.step_number}-${step.step_type}`} step={step} index={i} />)}
              </div>
            )}
          </motion.div>
        </div>

        {/* Right — Metadata */}
        <div className="md:col-span-4 space-y-4">
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs">Assessment Details</h3>
            <div className="space-y-3">
              {[
                { icon: 'tag', label: 'ID', value: assessment.id.slice(0, 8) + '...' },
                { icon: 'description', label: 'Type', value: assessment.input_type },
                { icon: 'schedule', label: 'Submitted', value: new Date(assessment.submitted_at).toLocaleString() },
                { icon: 'pending', label: 'Status', value: assessment.status },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-on-surface-variant text-[16px]">{item.icon}</span>
                  <span className="text-xs text-on-surface-variant w-16">{item.label}</span>
                  <span className="text-xs text-on-surface capitalize font-medium">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {assessment.detected_symptoms?.length ? (
            <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-secondary text-[18px]">medical_information</span>
                <h3 className="font-label-md text-on-surface uppercase tracking-wider text-xs">Detected Patterns</h3>
              </div>
              <div className="space-y-1.5">
                {assessment.detected_symptoms.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-surface-container-high rounded-lg">
                    <span className="material-symbols-outlined text-secondary text-[14px] mt-0.5 flex-shrink-0">arrow_forward</span>
                    <p className="text-xs text-on-surface-variant">{s}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="bg-error-container/10 border border-error/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-error text-[16px]">emergency</span>
              <h3 className="font-label-md text-error text-xs uppercase tracking-wider">Crisis Resources</h3>
            </div>
            <div className="space-y-1 text-xs text-on-surface-variant">
              <p>📞 <strong className="text-on-surface">988</strong> — Call/Text</p>
              <p>💬 Text <strong className="text-on-surface">HOME</strong> to 741741</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
