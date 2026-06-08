'use client';
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  risk_level?: string;
  resources?: string[];
  timestamp: Date;
}

const STARTERS = [
  "I've been feeling really hopeless lately",
  "I'm having constant panic attacks",
  "How do I help a suicidal friend?",
  "I've been isolating myself from everyone",
  "What are signs of a mental health crisis?",
  "I've been having dark thoughts recently",
];

const RISK_BADGE: Record<string, string> = {
  crisis: 'bg-error-container text-on-error-container',
  high: 'bg-error-container/50 text-error',
  moderate: 'bg-secondary-container text-on-secondary-container',
  low: 'bg-tertiary-container text-on-tertiary-container',
  safe: 'bg-primary-container text-on-primary-container',
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    id: '0', role: 'assistant', timestamp: new Date(),
    content: "Hello. I'm MINDWATCH Support — your AI mental health companion.\n\nI'm here to listen, provide clinical information, and connect you with the right resources. I'm not a replacement for professional care, but I can help you understand what you're experiencing and what steps to take.\n\nIf you're in immediate crisis, please call 988 (Suicide & Crisis Lifeline) or text HOME to 741741.\n\nHow are you feeling today?",
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setInput('');
    setLoading(true);
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content, timestamp: new Date() }]);

    try {
      const res = await fetch(`${API_BASE}/consumer/analyze-situation`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ situation: content }),
      });
      const json = await res.json();
      if (json.error) throw new Error(json.error.message);
      const data = json.data;

      let reply = data.explanation;
      if (data.immediate_actions?.length) {
        reply += '\n\n**What you can do:**\n' + data.immediate_actions.map((a: string, i: number) => `${i + 1}. ${a}`).join('\n');
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: reply,
        risk_level: data.risk_level,
        resources: data.report_to,
        timestamp: new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'assistant', timestamp: new Date(),
        content: "I'm having trouble connecting right now. If you're in crisis, please call 988 immediately.",
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-[1440px] mx-auto px-4 md:px-8 mt-4">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-120px)]">

        {/* Sidebar */}
        <div className="hidden md:flex md:col-span-3 flex-col gap-4">
          <div className="bg-surface-container rounded-xl border border-outline-variant p-4">
            <h3 className="font-label-md text-on-surface uppercase tracking-wider mb-3 text-xs">Quick Topics</h3>
            <div className="space-y-1.5">
              {STARTERS.map((s, i) => (
                <button key={i} onClick={() => send(s)}
                  className="w-full text-left text-xs text-on-surface-variant hover:text-primary hover:bg-surface-container-highest px-3 py-2 rounded-lg transition-all">
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-error-container/20 border border-error/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-error text-[18px]">emergency</span>
              <h3 className="font-label-md text-error text-xs uppercase tracking-wider">Crisis Lines</h3>
            </div>
            <div className="space-y-1 text-xs text-on-surface-variant">
              <p>📞 <strong className="text-on-surface">988</strong> — Suicide & Crisis Lifeline</p>
              <p>💬 Text <strong className="text-on-surface">HOME</strong> to 741741</p>
              <p>🌐 <strong className="text-on-surface">988lifeline.org</strong></p>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="md:col-span-9 flex flex-col bg-surface-container rounded-xl border border-outline-variant overflow-hidden">
          {/* Chat Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-outline-variant">
            <div className="w-9 h-9 rounded-full bg-primary-container border border-primary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-[18px]">psychology</span>
            </div>
            <div>
              <p className="font-label-md text-on-surface text-sm">MINDWATCH Support</p>
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
                <p className="text-xs text-on-surface-variant">Powered by Groq + Clinical NLP</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
            {messages.map((msg, i) => (
              <motion.div key={msg.id}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-primary-container border border-primary/30 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                    <span className="material-symbols-outlined text-primary text-[14px]">psychology</span>
                  </div>
                )}
                <div className="max-w-[75%]">
                  <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-primary text-on-primary rounded-tr-sm'
                      : 'bg-surface-container-high border border-outline-variant text-on-surface rounded-tl-sm'
                  }`}>
                    {msg.content}
                  </div>
                  {msg.risk_level && msg.risk_level !== 'safe' && (
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-label-md capitalize ${RISK_BADGE[msg.risk_level] ?? 'bg-surface-container text-on-surface'}`}>
                        {msg.risk_level} risk
                      </span>
                      {msg.resources?.slice(0, 2).map((r, i) => (
                        <span key={i} className="text-xs text-on-surface-variant bg-surface-container border border-outline-variant px-2 py-0.5 rounded-full">{r}</span>
                      ))}
                    </div>
                  )}
                  <p className="text-[10px] text-on-surface-variant mt-1 px-1">
                    {msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-surface-container-highest border border-outline-variant flex items-center justify-center ml-2 mt-1 flex-shrink-0">
                    <span className="material-symbols-outlined text-on-surface text-[14px]">person</span>
                  </div>
                )}
              </motion.div>
            ))}

            <AnimatePresence>
              {loading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-2 mb-4">
                  <div className="w-7 h-7 rounded-full bg-primary-container border border-primary/30 flex items-center justify-center flex-shrink-0">
                    <span className="material-symbols-outlined text-primary text-[14px]">psychology</span>
                  </div>
                  <div className="bg-surface-container-high border border-outline-variant rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex items-center gap-1">
                      {[0, 1, 2].map(i => (
                        <motion.div key={i} className="w-1.5 h-1.5 bg-primary rounded-full"
                          animate={{ y: [0, -4, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }} />
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-outline-variant p-3">
            {messages.length === 1 && (
              <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
                {STARTERS.slice(0, 3).map((s, i) => (
                  <button key={i} onClick={() => send(s)}
                    className="flex-shrink-0 text-xs text-on-surface-variant bg-surface-container-high border border-outline-variant hover:border-primary/50 px-3 py-1.5 rounded-full transition-all whitespace-nowrap">
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <textarea value={input} onChange={e => setInput(e.target.value)} rows={2} disabled={loading}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder="Share what's on your mind..."
                className="flex-1 bg-surface-container-high border border-outline-variant rounded-xl px-4 py-2.5 text-on-surface placeholder-on-surface-variant/50 text-sm resize-none focus:outline-none focus:border-primary transition-colors" />
              <button onClick={() => send()} disabled={!input.trim() || loading}
                className="w-10 h-10 bg-primary text-on-primary rounded-full flex items-center justify-center glow-btn disabled:opacity-40 flex-shrink-0 self-end transition-colors hover:bg-primary-fixed">
                <span className="material-symbols-outlined text-[20px]">send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
