import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, Filter, Search } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { projectApi } from '../../services/api';
import type { ProjectSummary } from '../../services/api';

const ProjectList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const query = searchParams.get('q') || '';
  const risk = searchParams.get('risk') || '';
  const page = Number(searchParams.get('page') || '1');

  useEffect(() => {
    setLoading(true);
    setError('');
    projectApi.list({ q: query || undefined, risk: risk || undefined, page, limit: 25 })
      .then(({ data }) => { setProjects(data.projects); setTotal(data.total); })
      .catch(() => setError('Unable to load project data.'))
      .finally(() => setLoading(false));
  }, [query, risk, page]);

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    if (key !== 'page') next.delete('page');
    setSearchParams(next);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-black">Project Directory</h1>
        <p className="text-sm text-slate-500">Search and analyze authorized infrastructure projects.</p>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row gap-3 bg-slate-50/50">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input aria-label="Search projects" value={query} onChange={(event) => updateParam('q', event.target.value)} placeholder="Search by name, ID, code or agency..." className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-government-blue" />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select aria-label="Filter by risk" value={risk} onChange={(event) => updateParam('risk', event.target.value)} className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm">
              <option value="">All risk levels</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option>
            </select>
          </div>
        </div>
        {loading && <p className="p-8 text-center text-slate-500">Loading project data...</p>}
        {error && <p className="p-8 text-center text-red-600">{error}</p>}
        {!loading && !error && projects.length === 0 && <p className="p-8 text-center text-slate-500">No projects found.</p>}
        {!loading && !error && projects.length > 0 && <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200"><tr><th className="px-6 py-4">Project</th><th className="px-6 py-4">Ministry / Agency</th><th className="px-6 py-4">State / Sector</th><th className="px-6 py-4">Progress</th><th className="px-6 py-4">Risk</th><th className="px-6 py-4" /></tr></thead>
            <tbody className="divide-y divide-slate-100">{projects.map((project) => <tr key={project.project_code} className="hover:bg-blue-50/30">
              <td className="px-6 py-4"><Link className="font-bold text-government-blue" to={`/dashboard/projects/${encodeURIComponent(project.project_code)}`}>{project.project_code}</Link><div className="text-slate-700">{project.project_name}</div></td>
              <td className="px-6 py-4"><div>{project.ministry || 'No data available'}</div><div className="text-xs text-slate-500">{project.agency || 'No data available'}</div></td>
              <td className="px-6 py-4"><div>{project.state || 'No data available'}</div><div className="text-xs text-slate-500">{project.sector || 'No data available'}</div></td>
              <td className="px-6 py-4"><div className="flex items-center gap-2"><span>{project.physical_progress == null ? 'No data available' : `${project.physical_progress}%`}</span>{project.physical_progress != null && <div className="w-20 h-2 bg-slate-100 rounded-full"><div className="h-full bg-government-blue rounded-full" style={{ width: `${Math.min(project.physical_progress, 100)}%` }} /></div>}</div></td>
              <td className="px-6 py-4"><span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold border border-slate-200">{['HIGH', 'CRITICAL'].includes(project.overall_risk || '') && <AlertTriangle className="w-3 h-3" />}{project.overall_risk || 'UNASSESSED'}</span></td>
              <td className="px-6 py-4 text-right"><Link className="inline-flex items-center gap-1 text-government-blue" to={`/dashboard/projects/${encodeURIComponent(project.project_code)}`}>Analyze <ArrowRight className="w-3.5 h-3.5" /></Link></td>
            </tr>)}</tbody>
          </table>
        </div>}
        {!loading && total > 25 && <div className="px-6 py-4 border-t border-slate-200 flex justify-between text-sm"><span>{total} authorized projects</span><button disabled={page <= 1} onClick={() => updateParam('page', String(page - 1))} className="px-3 py-1 border rounded disabled:opacity-40">Previous</button><button disabled={page * 25 >= total} onClick={() => updateParam('page', String(page + 1))} className="px-3 py-1 border rounded disabled:opacity-40">Next</button></div>}
      </div>
    </div>
  );
};

export default ProjectList;
