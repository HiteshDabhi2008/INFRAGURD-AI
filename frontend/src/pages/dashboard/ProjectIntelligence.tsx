import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, ArrowLeft, Bot, Clock, IndianRupee, Send } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { aiApi, projectApi } from '../../services/api';
import type { ProjectDetail } from '../../services/api';

const ProjectIntelligence = () => {
  const { id = '' } = useParams();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [prediction, setPrediction] = useState<Record<string, unknown> | null>(null);
  const [predictionError, setPredictionError] = useState('');

  useEffect(() => { projectApi.detail(id).then(({ data }) => setProject(data)).catch(() => setError('Unable to load project data.')); }, [id]);

  const runRisk = () => { setPredictionError(''); projectApi.riskPrediction(id).then(({ data }) => setPrediction(data)).catch(() => setPredictionError('Risk model output is unavailable for this project.')); };
  const ask = () => { if (!question.trim()) return; setAnswer(''); aiApi.chat(question, id).then(({ data }) => setAnswer(data.answer)).catch(() => setAnswer('AI service unavailable. No generated answer was returned.')); };

  if (error) return <p className="p-8 text-center text-red-600">{error}</p>;
  if (!project) return <p className="p-8 text-center text-slate-500">Loading project data...</p>;
  const latest = project.history[project.history.length - 1];

  return <div className="space-y-6">
    <Link to="/dashboard/projects" className="inline-flex items-center text-sm text-slate-500 hover:text-government-blue"><ArrowLeft className="w-4 h-4 mr-1" /> Back to Directory</Link>
    <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-bold text-black">{project.project_name}</h1><span className="px-2.5 py-1 bg-slate-200 text-slate-700 text-xs font-bold rounded-md">{project.project_code}</span></div><p className="text-sm text-slate-500 mt-1">{project.ministry || 'No ministry available'} · {project.agency || 'No agency available'} · {project.state || 'No state available'}</p></div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">{[['Original approved cost', project.original_cost == null ? 'No data available' : `₹${project.original_cost} Cr`, IndianRupee], ['Latest revised cost', project.revised_cost == null ? 'No data available' : `₹${project.revised_cost} Cr`, IndianRupee], ['Cumulative expenditure', project.cumulative_expenditure == null ? 'No data available' : `₹${project.cumulative_expenditure} Cr`, TrendingUpIcon], ['Physical progress', project.physical_progress == null ? 'No data available' : `${project.physical_progress}%`, Activity]].map(([label, value, Icon]) => <div key={String(label)} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm"><Icon className="w-5 h-5 text-government-blue mb-3" /><div className="font-bold text-lg">{value as string}</div><div className="text-xs text-slate-500">{label as string}</div></div>)}</div>
    <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><div className="flex justify-between items-center mb-4"><h2 className="font-bold flex items-center gap-2"><Activity className="w-5 h-5 text-government-blue" /> Monthly History</h2><span className="text-sm text-slate-500">{latest?.report_month || 'No data available'}</span></div>{project.history.length === 0 ? <p className="text-slate-500">Data unavailable for this reporting month.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="py-3">Month</th><th className="py-3">Progress</th><th className="py-3">Cumulative expenditure</th><th className="py-3">Revised cost</th></tr></thead><tbody>{project.history.map((item) => <tr key={item.id} className="border-b border-slate-100"><td className="py-3">{item.report_month}</td><td className="py-3">{item.physical_progress == null ? 'No data available' : `${item.physical_progress}%`}</td><td className="py-3">{item.cumulative_expenditure == null ? 'No data available' : `₹${item.cumulative_expenditure} Cr`}</td><td className="py-3">{item.revised_cost == null ? 'No data available' : `₹${item.revised_cost} Cr`}</td></tr>)}</tbody></table></div>}</section>
    <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><div className="flex items-center justify-between"><h2 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-amber-600" /> Risk and predictions</h2><button onClick={runRisk} className="px-3 py-2 bg-government-blue text-white rounded-lg text-sm">Run risk assessment</button></div>{project.overall_risk ? <p className="mt-4">Persisted risk: <strong>{project.overall_risk}</strong> {project.risk_score == null ? '' : `(${project.risk_score}/100)`}</p> : <p className="mt-4 text-slate-500">No persisted risk assessment is available.</p>}{predictionError && <p className="mt-3 text-red-600">{predictionError}</p>}{prediction && <pre className="mt-4 p-4 bg-slate-50 rounded-lg overflow-auto text-xs">{JSON.stringify(prediction, null, 2)}</pre>}</section>
    <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><h2 className="font-bold flex items-center gap-2 mb-4"><Bot className="w-5 h-5 text-government-blue" /> Project AI assistant</h2>{answer && <div className="p-4 bg-slate-50 rounded-lg whitespace-pre-wrap mb-4">{answer}</div>}<div className="flex gap-2"><input value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && ask()} placeholder={`Ask about ${project.project_name}...`} className="flex-1 px-4 py-3 border rounded-lg" /><button onClick={ask} className="px-4 py-3 bg-government-blue text-white rounded-lg" aria-label="Ask AI"><Send className="w-4 h-4" /></button></div></section>
  </div>;
};

const TrendingUpIcon = Clock;
export default ProjectIntelligence;
