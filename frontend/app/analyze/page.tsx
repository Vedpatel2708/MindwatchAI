'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { submitAssessment } from '@/lib/api';

const EXAMPLES = [
  { icon: 'menu_book', type: 'journal', label: 'Journal Entry', preview: "I haven't been able to get out of bed...", text: "I haven't been able to get out of bed for the past week. Everything feels pointless and I'm so tired all the time. I used to love painting but I can't even pick up a brush. I don't know what's wrong with me." },
  { icon: 'chat', type: 'chat', label: 'Message', preview: "I just can't do this anymore...", text: "I just can't do this anymore. I've been having these dark thoughts and I don't know how to make them stop. I feel like everyone would be better off without me." },
  { icon: 'description', type: 'note', label: 'Clinical Note', preview: "Patient presents with persistent low mood...", text: "Patient presents with persistent low mood for 3 weeks, reports anhedonia, hypersomnia, and difficulty concentrating. Denies active suicidal ideation but expresses passive death wish. PHQ-9 score: 18." },
];

const INPUT_TYPES = [
  { value: 'journal', label: 'Journal', icon: 'menu_book' },
  { value: 'chat', label: 'Message', icon: 'chat' },
  { value: 'note', label: 'Clinical Note', icon: 'description' },
  { value: 'speech', label: 'Transcript', icon: 'record_voice_over' },
];

export default function AnalyzePage() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [inputType, setInputType] = useState('journal');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (text.trim().length < 20) { setError('Please enter at least 20 characters.'); return; }
    setLoading(true); setError('');
    try {
      const result = await submitAssessment({ input_text: text, input_type: inputType });
      // Backend returns { assessment_id, risk_level, crisis_score, status }
      const assessmentId = result.assessment_id;
      if (!assessmentId) throw new Error('No assessment ID returned from server');
      router.push(`/assessments/${assessmentId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed. Is the backend running?');
      setLoading(false);
    }
  };

  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 mt-4 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="font-display text-2xl md:text-3xl font-semibold text-on-surface">Text Analysis</h1>
        <p className="font-body-md text-on-surface-variant mt-1">Multi-modal clinical screening using BioBERT + 3 ML classifiers + LangChain ReAct agent.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Main Input Area */}
        <div className="md:col-span-8 space-y-4">

          {/* Input Type Selector */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <p className="font-label-md text-on-surface-variant uppercase tracking-wider mb-3 text-xs">Input Type</p>
            <div className="grid grid-cols-4 gap-2">
              {INPUT_TYPES.map(t => (
                <button key={t.value} onClick={() => setInputType(t.value)}
                  className={`rounded-xl p-3 text-center transition-all border text-sm ${
                    inputType === t.value
                      ? 'bg-primary text-on-primary border-primary glow-btn'
                      : 'bg-surface-container-high border-outline-variant text-on-surface-variant hover:border-primary/50'
                  }`}>
                  <span className="material-symbols-outlined text-[20px] block mb-1">{t.icon}</span>
                  <span className="font-label-md text-xs">{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Text Input */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4 glow-effect">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-primary text-[20px]">psychology</span>
              <h2 className="font-title-lg text-on-surface text-base">Clinical Text Input</h2>
            </div>
            <textarea
              value={text}
              onChange={e => { setText(e.target.value); setError(''); }}
              placeholder="Paste a journal entry, clinical note, chat message, or speech transcript here for AI-powered mental health screening..."
              rows={12}
              className="w-full bg-surface-container-high border border-outline-variant rounded-xl px-4 py-3 text-on-surface placeholder-on-surface-variant/40 font-body-md resize-none focus:outline-none focus:border-primary transition-colors"
            />
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-3">
                <span className="text-xs text-on-surface-variant">{wordCount} words</span>
                <span className="text-xs text-on-surface-variant">{text.length} chars</span>
                {text.length >= 20 && (
                  <span className="text-xs text-primary flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">check_circle</span>
                    Ready to analyze
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {text && (
                  <button onClick={() => setText('')} className="text-xs text-on-surface-variant hover:text-primary transition-colors px-3 py-1.5 rounded-full hover:bg-surface-container-highest">
                    Clear
                  </button>
                )}
                <button
                  onClick={handleSubmit}
                  disabled={loading || text.length < 20}
                  className="bg-primary text-on-primary hover:bg-primary-fixed font-label-md px-6 py-2 rounded-full flex items-center gap-2 font-semibold glow-btn transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                  {loading ? (
                    <>
                      <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[18px]">document_scanner</span>
                      Run Full Analysis
                    </>
                  )}
                </button>
              </div>
            </div>
            {error && (
              <p className="text-error text-xs mt-2 flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">error</span>
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="md:col-span-4 space-y-4">
          {/* What happens */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs">Analysis Pipeline</h3>
            <div className="space-y-3">
              {[
                { icon: 'hub', label: 'BioBERT Embeddings', desc: 'Semantic similarity vs DSM-5 anchors' },
                { icon: 'model_training', label: 'PHQ-9 Classifier', desc: 'Depression severity scoring' },
                { icon: 'warning', label: 'Crisis Detector', desc: 'Suicidality risk assessment' },
                { icon: 'sentiment_very_dissatisfied', label: 'Emotion Classifier', desc: '8-class emotion prediction' },
                { icon: 'smart_toy', label: 'ReAct Agent', desc: 'Groq LLM clinical investigation' },
              ].map((s, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-full bg-primary-container border border-primary/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="material-symbols-outlined text-primary text-[14px]">{s.icon}</span>
                  </div>
                  <div>
                    <p className="font-label-md text-on-surface text-xs">{s.label}</p>
                    <p className="text-xs text-on-surface-variant">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Examples */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs">Try an Example</h3>
            <div className="space-y-2">
              {EXAMPLES.map((ex, i) => (
                <button key={i}
                  onClick={() => { setText(ex.text); setInputType(ex.type); }}
                  className="w-full text-left p-3 bg-surface-container-high border border-outline-variant rounded-xl hover:border-primary/50 transition-all group">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="material-symbols-outlined text-primary text-[16px]">{ex.icon}</span>
                    <span className="font-label-md text-on-surface text-xs uppercase tracking-wider">{ex.label}</span>
                  </div>
                  <p className="text-xs text-on-surface-variant line-clamp-2">{ex.preview}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="bg-error-container/10 border border-error/20 rounded-xl p-3">
            <div className="flex items-start gap-2">
              <span className="material-symbols-outlined text-error text-[16px] mt-0.5">info</span>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                For educational and research use only. Not a substitute for professional mental health care.
                If in crisis: call <strong className="text-on-surface">988</strong>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
