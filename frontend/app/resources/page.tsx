'use client';
/**
 * frontend/app/resources/page.tsx — MINDWATCH Knowledge Base (RAG)
 *
 * Users can ask any mental health question and get answers grounded
 * in a curated, evidence-based knowledge base.
 *
 * RAG Pipeline shown to user:
 *   1. Query embedded → 2. Top-3 chunks retrieved → 3. Groq generates answer
 */

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface Source {
  title: string;
  category: string;
  source: string;
  tags: string[];
  similarity: number;
  excerpt: string;
}

interface RAGResult {
  answer: string;
  sources: Source[];
  query: string;
  retrieval_count: number;
}

const CATEGORIES = [
  { value: '', label: 'All Topics', icon: 'apps' },
  { value: 'depression', label: 'Depression', icon: 'sentiment_very_dissatisfied' },
  { value: 'anxiety', label: 'Anxiety', icon: 'psychology_alt' },
  { value: 'crisis', label: 'Crisis & Safety', icon: 'emergency' },
  { value: 'coping', label: 'Coping Skills', icon: 'self_improvement' },
  { value: 'therapy', label: 'Therapy', icon: 'medical_information' },
  { value: 'self-care', label: 'Self-Care', icon: 'spa' },
];

const SUGGESTED_QUESTIONS = [
  "What are the symptoms of depression?",
  "How can I manage a panic attack right now?",
  "What is CBT and how does it help?",
  "How do I help someone who is suicidal?",
  "What exercises help with anxiety?",
  "How does sleep affect mental health?",
  "What is behavioral activation for depression?",
  "How do grounding techniques work?",
];

const CATEGORY_COLORS: Record<string, string> = {
  depression: 'bg-secondary-container text-on-secondary-container',
  anxiety: 'bg-tertiary-container text-on-tertiary-container',
  crisis: 'bg-error-container text-on-error-container',
  coping: 'bg-primary-container text-on-primary-container',
  therapy: 'bg-surface-container-highest text-on-surface',
  'self-care': 'bg-tertiary-container text-on-tertiary-container',
};

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const colorClass = CATEGORY_COLORS[source.category] ?? 'bg-surface-container text-on-surface';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className="bg-surface-container-high border border-outline-variant rounded-xl p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full font-label-md capitalize ${colorClass}`}>
              {source.category}
            </span>
            <span className="text-xs text-on-surface-variant font-mono">
              {(source.similarity * 100).toFixed(0)}% match
            </span>
          </div>
          <p className="font-label-md text-on-surface text-sm font-medium">{source.title}</p>
          <p className="text-xs text-on-surface-variant mt-0.5">Source: {source.source}</p>
        </div>
        <button onClick={() => setExpanded(e => !e)}
          className="text-on-surface-variant hover:text-primary transition-colors flex-shrink-0">
          <span className="material-symbols-outlined text-[18px]">
            {expanded ? 'expand_less' : 'expand_more'}
          </span>
        </button>
      </div>

      <p className="text-xs text-on-surface-variant leading-relaxed">
        {expanded ? source.excerpt : source.excerpt.slice(0, 120) + '...'}
      </p>

      {source.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {source.tags.slice(0, 4).map(tag => (
            <span key={tag} className="text-[10px] text-on-surface-variant bg-surface-container border border-outline-variant px-1.5 py-0.5 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

export default function ResourcesPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGResult | null>(null);
  const [error, setError] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState('');

  const handleQuery = async (q?: string) => {
    const searchQuery = q ?? query;
    if (searchQuery.trim().length < 5) { setError('Please enter a question.'); return; }
    setLoading(true); setError(''); setResult(null);

    try {
      const res = await fetch(`${API_BASE}/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          top_k: 3,
          category_filter: category || null,
        }),
      });
      const json = await res.json();
      if (json.error) throw new Error(json.error.message);
      setResult(json.data);
      if (q) setQuery(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Query failed. Make sure the backend is running and knowledge base is ingested.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    setIngesting(true); setIngestMessage('');
    try {
      const res = await fetch(`${API_BASE}/rag/ingest`, { method: 'POST' });
      const json = await res.json();
      if (json.error) throw new Error(json.error.message);
      setIngestMessage(`✅ Ingested ${json.data.success} documents successfully`);
    } catch (e) {
      setIngestMessage(`❌ ${e instanceof Error ? e.message : 'Ingestion failed'}`);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 mt-4 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="font-display text-2xl md:text-3xl font-semibold text-on-surface">
            Knowledge Base
          </h1>
          <p className="font-body-md text-on-surface-variant mt-1">
            Evidence-based mental health information powered by RAG — Retrieval-Augmented Generation.
          </p>
        </div>
        <button onClick={handleIngest} disabled={ingesting}
          className="text-xs text-on-surface-variant border border-outline-variant px-3 py-1.5 rounded-full hover:border-primary hover:text-primary transition-all disabled:opacity-40 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[14px]">
            {ingesting ? 'sync' : 'database'}
          </span>
          {ingesting ? 'Building index...' : 'Build Knowledge Index'}
        </button>
      </div>

      {ingestMessage && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="text-sm text-on-surface bg-surface-container border border-outline-variant px-4 py-2 rounded-xl">
          {ingestMessage}
        </motion.p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

        {/* Left — Search */}
        <div className="md:col-span-8 space-y-4">

          {/* Category Filter */}
          <div className="flex gap-2 overflow-x-auto pb-1">
            {CATEGORIES.map(cat => (
              <button key={cat.value} onClick={() => setCategory(cat.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-label-md transition-all whitespace-nowrap flex-shrink-0 border ${
                  category === cat.value
                    ? 'bg-primary text-on-primary border-primary glow-btn'
                    : 'bg-surface-container border-outline-variant text-on-surface-variant hover:border-primary/50'
                }`}>
                <span className="material-symbols-outlined text-[14px]">{cat.icon}</span>
                {cat.label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="bg-surface-container border border-outline-variant rounded-xl p-4 glow-effect">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-primary text-[20px]">search</span>
              <h2 className="font-label-md text-on-surface text-sm uppercase tracking-wider">
                Ask the Knowledge Base
              </h2>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={e => { setQuery(e.target.value); setError(''); }}
                onKeyDown={e => { if (e.key === 'Enter') handleQuery(); }}
                placeholder="e.g. What are CBT techniques for depression?"
                className="flex-1 bg-surface-container-high border border-outline-variant rounded-xl px-4 py-2.5 text-on-surface placeholder-on-surface-variant/50 text-sm focus:outline-none focus:border-primary transition-colors"
              />
              <button onClick={() => handleQuery()} disabled={loading || query.length < 5}
                className="bg-primary text-on-primary hover:bg-primary-fixed px-4 py-2.5 rounded-xl font-label-md text-sm glow-btn transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0">
                {loading ? (
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                ) : (
                  <span className="material-symbols-outlined text-[18px]">search</span>
                )}
                Search
              </button>
            </div>
            {error && (
              <p className="text-error text-xs mt-2 flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">error</span>
                {error}
              </p>
            )}
          </div>

          {/* Results */}
          <AnimatePresence>
            {result && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">

                {/* RAG Pipeline badge */}
                <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                  <span className="material-symbols-outlined text-primary text-[14px]">hub</span>
                  <span>Retrieved {result.retrieval_count} relevant knowledge chunks → Generated answer with Groq LLM</span>
                </div>

                {/* Answer */}
                <div className="bg-surface-container border border-outline-variant rounded-xl p-5 border-l-4 border-l-primary glow-effect">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="material-symbols-outlined text-primary text-[20px]">psychology</span>
                    <h3 className="font-label-md text-on-surface uppercase tracking-wider text-xs">AI Answer</h3>
                    <span className="text-xs text-on-surface-variant ml-auto">Grounded in knowledge base</span>
                  </div>
                  <div className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">
                    {result.answer}
                  </div>
                </div>

                {/* Sources */}
                {result.sources.length > 0 && (
                  <div>
                    <p className="font-label-md text-on-surface-variant uppercase tracking-wider text-xs mb-3 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">menu_book</span>
                      Sources ({result.sources.length})
                    </p>
                    <div className="space-y-3">
                      {result.sources.map((source, i) => (
                        <SourceCard key={i} source={source} index={i} />
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Empty state */}
          {!result && !loading && (
            <div className="text-center py-12 opacity-60">
              <span className="material-symbols-outlined text-outline text-[56px] block mb-3">menu_book</span>
              <p className="text-on-surface font-body-md font-medium">Ask anything about mental health</p>
              <p className="text-on-surface-variant text-sm mt-1">
                Answers grounded in evidence-based clinical knowledge
              </p>
            </div>
          )}
        </div>

        {/* Right — Suggested Questions */}
        <div className="md:col-span-4 space-y-4">
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">lightbulb</span>
              Suggested Questions
            </h3>
            <div className="space-y-2">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <motion.button key={i} onClick={() => handleQuery(q)}
                  initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ x: 4 }}
                  className="w-full text-left text-xs text-on-surface-variant hover:text-primary hover:bg-surface-container-highest px-3 py-2 rounded-lg transition-all flex items-center gap-2 group">
                  <span className="material-symbols-outlined text-[14px] text-outline group-hover:text-primary transition-colors">arrow_forward</span>
                  {q}
                </motion.button>
              ))}
            </div>
          </div>

          {/* How RAG Works */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs flex items-center gap-2">
              <span className="material-symbols-outlined text-tertiary text-[16px]">schema</span>
              How RAG Works
            </h3>
            <div className="space-y-3">
              {[
                { step: '1', icon: 'search', label: 'Retrieve', desc: 'Your query is embedded and matched against 20+ knowledge documents using cosine similarity' },
                { step: '2', icon: 'hub', label: 'Augment', desc: 'Top-3 most relevant knowledge chunks are injected into the LLM context as grounding' },
                { step: '3', icon: 'psychology', label: 'Generate', desc: 'Groq LLM generates an answer using only the retrieved context — no hallucination' },
              ].map(item => (
                <div key={item.step} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-container border border-primary/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-[10px] text-primary font-bold">{item.step}</span>
                  </div>
                  <div>
                    <p className="font-label-md text-on-surface text-xs">{item.label}</p>
                    <p className="text-xs text-on-surface-variant mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Crisis resources */}
          <div className="bg-error-container/10 border border-error/20 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-error text-[16px]">emergency</span>
              <p className="font-label-md text-error text-xs uppercase">In Crisis?</p>
            </div>
            <p className="text-xs text-on-surface-variant">
              Call <strong className="text-on-surface">988</strong> · Text HOME to <strong className="text-on-surface">741741</strong>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
