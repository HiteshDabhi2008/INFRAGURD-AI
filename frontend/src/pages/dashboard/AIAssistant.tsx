import { useState } from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';
import { aiApi } from '../../services/api';

const suggestions = ['Show high-risk projects', 'Show critical projects', 'Which projects need attention?', 'Give ministry-wise risk summary'];

const AIAssistant = () => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const ask = async (message = query) => {
    if (!message.trim()) return;
    setQuery(message); setLoading(true); setError('');
    try { const { data } = await aiApi.chat(message); setAnswer(data.answer); }
    catch { setError('AI service unavailable. No generated answer was returned.'); }
    finally { setLoading(false); }
  };
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">InfraGuard AI</h1><p className="text-sm text-slate-500">Answers are grounded in authorized project data and available model outputs.</p></div><div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 min-h-[28rem] flex flex-col"><div className="flex-1">{!answer && !error && <div className="text-slate-500 flex items-center gap-2"><Bot className="w-5 h-5" /> Ask a question to retrieve grounded project intelligence.</div>}{loading && <p className="text-slate-500">Retrieving authorized context...</p>}{error && <p className="text-red-600">{error}</p>}{answer && <div className="whitespace-pre-wrap bg-slate-50 rounded-lg p-4">{answer}</div>}</div><div className="flex flex-wrap gap-2 mb-4">{suggestions.map((item) => <button key={item} onClick={() => ask(item)} className="px-3 py-2 text-sm border rounded-lg hover:border-government-blue">{item}</button>)}</div><div className="flex gap-2"><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && ask()} placeholder="Ask about projects, risks, or predictions..." className="flex-1 px-4 py-3 border rounded-lg" /><button disabled={loading} onClick={() => ask()} className="px-4 py-3 bg-government-blue text-white rounded-lg disabled:opacity-50" aria-label="Send question"><Send className="w-4 h-4" /></button></div><div className="mt-3 text-xs text-slate-400 flex items-center gap-1"><Sparkles className="w-3 h-3" /> Numerical answers come from retrieved data, not generated guesses.</div></div></div>;
};
export default AIAssistant;
