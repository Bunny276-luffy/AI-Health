'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Sparkles, Loader2, AlertTriangle } from 'lucide-react';

interface VQAPanelProps { scanContext: any; apiBase: string; }
interface Message { role: 'user' | 'assistant'; content: string; timestamp: number; }

const SUGGESTIONS = ["What does the epistemic uncertainty indicate here?", "Is the conformal prediction interval reliable?", "Explain the radiomics texture features.", "What are the clinical implications of this probability score?"];

export const VQAPanel: React.FC<VQAPanelProps> = ({ scanContext, apiBase }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSubmit = async (q: string) => {
    if (!q.trim() || !scanContext) return;
    const newMsg: Message = { role: 'user', content: q, timestamp: Date.now() };
    setMessages((prev) => [...prev, newMsg]); setInput(''); setIsStreaming(true);
    
    // Add empty assistant message that will be streamed into
    setMessages((prev) => [...prev, { role: 'assistant', content: '', timestamp: Date.now() }]);

    try {
      const response = await fetch(`${apiBase}/vqa/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, scan_context: scanContext })
      });
      if (!response.body) throw new Error('No stream');
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') { setIsStreaming(false); break; }
            try {
              const parsed = JSON.parse(data);
              setMessages((prev) => {
                const newArr = [...prev];
                newArr[newArr.length - 1].content += parsed.chunk;
                return newArr;
              });
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const newArr = [...prev];
        newArr[newArr.length - 1].content = "Error: Could not connect to AI assistant. Make sure the backend is running and ANTHROPIC_API_KEY is set in .env.";
        return newArr;
      });
    } finally { setIsStreaming(false); }
  };

  if (!scanContext) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3"><MessageSquare className="text-sky-400" size={20} /><h3 className="text-slate-100 font-semibold text-sm">Clinical Assistant</h3></div>
        <p className="text-slate-500 text-xs italic">Upload and analyze a scan first to ask questions.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl flex flex-col h-[500px]">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2"><Sparkles className="text-amber-400" size={18} /><h3 className="text-slate-100 font-semibold text-sm">Grounded AI Assistant</h3></div>
        <div className="flex items-center gap-1.5 text-[10px] text-amber-500 bg-amber-500/10 px-2 py-1 rounded-full"><AlertTriangle size={12} /><span>Not a medical diagnosis</span></div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col justify-end">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-auto">
              {SUGGESTIONS.map((s, i) => <button key={i} onClick={() => handleSubmit(s)} className="text-left text-xs bg-slate-800/50 hover:bg-slate-800 text-slate-300 p-3 rounded-lg border border-slate-700 transition-colors">{s}</button>)}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-3 rounded-xl text-sm ${msg.role === 'user' ? 'bg-sky-600 text-white rounded-tr-sm' : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-sm'}`}>
                {msg.content}
                {isStreaming && i === messages.length - 1 && <span className="inline-block w-1.5 h-4 ml-1 bg-amber-400 animate-pulse align-middle" />}
              </div>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>

      <div className="p-3 border-t border-slate-800">
        <div className="relative">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !isStreaming && handleSubmit(input)} disabled={isStreaming} placeholder="Ask about the scan results..." className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-4 pr-10 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500 transition-colors disabled:opacity-50" />
          <button onClick={() => handleSubmit(input)} disabled={isStreaming || !input.trim()} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-sky-400 disabled:opacity-50 transition-colors">
            {isStreaming ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
};
