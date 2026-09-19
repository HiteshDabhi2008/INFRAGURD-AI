import { useEffect, useState } from 'react';
import { 
  AlertTriangle, 
  ArrowRight, 
  Filter, 
  PlusCircle, 
  Search, 
  ShieldAlert,
  PieChart,
  FolderPlus
} from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { projectApi } from '../../services/api';
import type { ProjectSummary } from '../../services/api';
import { MonthlyProjectUpdateModal } from '../../components/projects/MonthlyProjectUpdateModal';
import { AddNewProjectModal } from '../../components/projects/AddNewProjectModal';
import { useAuth } from '../../contexts/AuthContext';

const ProjectList = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [sectors, setSectors] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  
  const query = searchParams.get('q') || '';
  const sector = searchParams.get('sector') || '';
  const state = searchParams.get('state') || '';
  const risk = searchParams.get('risk') || '';
  const page = Number(searchParams.get('page') || '1');

  const canManageProjects = user?.authority_type !== 'Viewer / Auditor' && (user as any)?.canonical_role !== 'VIEWER_AUDITOR';

  useEffect(() => {
    projectApi.getSectors()
      .then(({ data }) => setSectors(data))
      .catch(() => {});
  }, []);

  const fetchProjects = () => {
    setLoading(true);
    setError('');
    projectApi.list({ 
      q: query || undefined, 
      sector: sector || undefined,
      state: state || undefined,
      risk: risk || undefined, 
      page, 
      limit: 25 
    })
      .then(({ data }) => { setProjects(data.projects); setTotal(data.total); })
      .catch(() => setError('Unable to load project data. You may not be authorized to view this sector.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProjects();
  }, [query, sector, state, risk, page]);

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    if (key !== 'page') next.delete('page');
    setSearchParams(next);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Explore Projects</h1>
          <p className="text-sm text-slate-500">Access infrastructure projects within your authorized scope.</p>
        </div>
        {canManageProjects && (
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="px-4 py-2 bg-government-blue hover:bg-blue-800 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
            >
              <FolderPlus className="w-4 h-4" /> + Add New Project
            </button>
            <button
              onClick={() => setIsUpdateModalOpen(true)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" /> + Add Monthly Update
            </button>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Filters Bar */}
        <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row gap-3 bg-slate-50/50">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              aria-label="Search projects" 
              value={query} 
              onChange={(event) => updateParam('q', event.target.value)} 
              placeholder="Search by project name, ID, code or agency..." 
              className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-government-blue bg-white" 
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Sector Filter */}
            <div className="flex items-center gap-1.5">
              <PieChart className="w-3.5 h-3.5 text-slate-400" />
              <select 
                aria-label="Filter by sector" 
                value={sector} 
                onChange={(event) => updateParam('sector', event.target.value)} 
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700"
              >
                <option value="">All Sectors</option>
                {sectors.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Risk Filter */}
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select 
                aria-label="Filter by risk" 
                value={risk} 
                onChange={(event) => updateParam('risk', event.target.value)} 
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700"
              >
                <option value="">All Risk Levels</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading && <p className="p-12 text-center text-slate-500">Loading authorized projects...</p>}
        {error && <p className="p-12 text-center text-red-600">{error}</p>}
        {!loading && !error && projects.length === 0 && (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <p className="font-semibold">No authorized projects found.</p>
            <p className="text-xs text-slate-400">Try clearing filters or verify your authorized operational sector / state.</p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-600 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4">Project ID & Name</th>
                  <th className="px-6 py-4">Ministry / Agency</th>
                  <th className="px-6 py-4">State / Sector</th>
                  <th className="px-6 py-4">Physical Progress</th>
                  <th className="px-6 py-4">Risk Level</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {projects.map((project) => (
                  <tr key={project.project_code} className="hover:bg-blue-50/30 transition-colors">
                    <td className="px-6 py-4">
                      <Link className="font-bold text-government-blue font-mono hover:underline" to={`/dashboard/projects/${encodeURIComponent(project.project_code)}`}>
                        {project.project_code}
                      </Link>
                      <div className="text-slate-800 font-medium line-clamp-1 max-w-md">{project.project_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-800 font-medium">{project.ministry || 'N/A'}</div>
                      <div className="text-xs text-slate-500">{project.agency || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-800">{project.state || 'N/A'}</div>
                      <span className="inline-block mt-0.5 px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[11px] font-semibold">
                        {project.sector || 'Unassigned'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 w-12">
                          {project.physical_progress == null ? 'N/A' : `${project.physical_progress}%`}
                        </span>
                        {project.physical_progress != null && (
                          <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-government-blue rounded-full" 
                              style={{ width: `${Math.min(project.physical_progress, 100)}%` }} 
                            />
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold border ${
                        project.overall_risk === 'CRITICAL' ? 'bg-red-50 text-red-700 border-red-200' :
                        project.overall_risk === 'HIGH' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        project.overall_risk === 'MEDIUM' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}>
                        {['HIGH', 'CRITICAL'].includes(project.overall_risk || '') && <AlertTriangle className="w-3 h-3" />}
                        {project.overall_risk || 'LOW'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg text-xs font-bold border border-red-200 transition-colors shadow-2xs"
                          to={`/dashboard/projects/${encodeURIComponent(project.project_code)}/risk`}
                          title="Deep Risk Assessment"
                        >
                          <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                          <span>Risk Assessment</span>
                        </Link>
                        <Link
                          className="inline-flex items-center gap-1 text-government-blue hover:underline text-xs font-bold px-2 py-1"
                          to={`/dashboard/projects/${encodeURIComponent(project.project_code)}`}
                        >
                          Details <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && total > 25 && (
          <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between text-sm bg-slate-50/50">
            <span className="text-slate-600 font-medium">{total} authorized projects in scope</span>
            <div className="flex items-center gap-2">
              <button 
                disabled={page <= 1} 
                onClick={() => updateParam('page', String(page - 1))} 
                className="px-3 py-1.5 border border-slate-300 rounded-lg bg-white disabled:opacity-40 hover:bg-slate-50 font-medium text-xs transition-colors"
              >
                Previous
              </button>
              <button 
                disabled={page * 25 >= total} 
                onClick={() => updateParam('page', String(page + 1))} 
                className="px-3 py-1.5 border border-slate-300 rounded-lg bg-white disabled:opacity-40 hover:bg-slate-50 font-medium text-xs transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <AddNewProjectModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          fetchProjects();
        }}
      />

      <MonthlyProjectUpdateModal
        isOpen={isUpdateModalOpen}
        onClose={() => setIsUpdateModalOpen(false)}
        onSuccess={fetchProjects}
      />
    </div>
  );
};

export default ProjectList;

