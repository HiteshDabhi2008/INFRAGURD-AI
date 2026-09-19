import React, { useState, useEffect } from 'react';
import { 
  PlusCircle, 
  CheckCircle, 
  AlertTriangle, 
  FileText, 
  ArrowRight, 
  Search, 
  RefreshCw, 
  Loader2, 
  ShieldAlert,
  Calendar,
  IndianRupee,
  Layers
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { projectApi } from '../../services/api';
import type { ProjectSummary } from '../../services/api';
import { AddNewProjectModal } from '../../components/projects/AddNewProjectModal';
import { useAuth } from '../../contexts/AuthContext';

const NewProjectsView: React.FC = () => {
  const { user } = useAuth();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const canManageProjects = user?.authority_type !== 'Viewer / Auditor' && (user as any)?.canonical_role !== 'VIEWER_AUDITOR';

  const fetchNewlyAdded = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await projectApi.getNewlyAdded(100);
      setProjects(response.data || []);
    } catch (err: any) {
      console.error('Failed to load newly added projects', err);
      setError(err?.response?.data?.detail || 'Failed to load newly registered projects.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNewlyAdded();
  }, []);

  const handleProjectCreated = (newCode: string) => {
    setSuccessBanner(`Project ${newCode} has been registered successfully and added to the official pipeline.`);
    fetchNewlyAdded();
    setTimeout(() => {
      setSuccessBanner(null);
    }, 6000);
  };

  // Filtered projects
  const filtered = projects.filter((p) => {
    const matchesSearch = 
      p.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.project_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.ministry && p.ministry.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (p.sector && p.sector.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (p.state && p.state.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const pStatus = (p.status || 'Ongoing').toUpperCase();
    const matchesStatus = 
      statusFilter === 'ALL' ||
      (statusFilter === 'ONGOING' && pStatus.includes('ONGOING')) ||
      (statusFilter === 'APPROVED' && pStatus.includes('APPROVED')) ||
      (statusFilter === 'REVIEW' && (pStatus.includes('REVIEW') || pStatus.includes('EVALUATION') || pStatus.includes('PENDING'))) ||
      (statusFilter === 'HIGH_RISK' && (p.overall_risk === 'HIGH' || p.overall_risk === 'CRITICAL'));

    return matchesSearch && matchesStatus;
  });

  // Calculate live summary figures
  const totalCount = projects.length;
  const highRiskCount = projects.filter((p) => p.overall_risk === 'HIGH' || p.overall_risk === 'CRITICAL').length;
  const totalCost = projects.reduce((acc, p) => acc + (p.revised_cost || p.original_cost || 0), 0);
  const avgProgress = totalCount > 0 
    ? Math.round(projects.reduce((acc, p) => acc + (p.physical_progress || 0), 0) / totalCount) 
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Newly Registered Projects</h1>
            <span className="px-2.5 py-0.5 bg-blue-50 text-government-blue text-xs font-semibold rounded-full border border-blue-200">
              Official IPMD Ingestion
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Browse recently onboarded national infrastructure initiatives, review telemetry, and track pipeline registration.
          </p>
        </div>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={fetchNewlyAdded}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-slate-600 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-100 transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-government-blue' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {canManageProjects ? (
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-government-blue text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors shadow-sm"
            >
              <PlusCircle className="w-4 h-4" />
              <span>+ Add New Project</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 text-slate-500 text-xs rounded-lg border border-slate-200">
              <ShieldAlert className="w-4 h-4 text-slate-400" />
              <span>Read-Only Viewer</span>
            </div>
          )}
        </div>
      </div>

      {/* Success Notification Banner */}
      {successBanner && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 flex items-center justify-between shadow-sm animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="text-sm font-medium text-emerald-900">{successBanner}</span>
          </div>
          <button 
            onClick={() => setSuccessBanner(null)} 
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-50 border border-rose-300 rounded-xl p-4 flex items-center gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
            <FileText className="w-6 h-6 text-government-blue" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{totalCount}</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
              Newly Added Pipeline
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-100">
            <IndianRupee className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              ₹{totalCost >= 1000 ? `${(totalCost / 1000).toFixed(1)}k` : totalCost.toLocaleString()} Cr
            </div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
              Committed Outlay
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
            <Layers className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{avgProgress}%</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
              Average Progress
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-amber-50 p-3 rounded-lg border border-amber-100">
            <AlertTriangle className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{highRiskCount}</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
              Flagged Risk Watch
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by code, title, ministry, sector..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-government-blue/20 focus:border-government-blue"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-government-blue"
          >
            <option value="ALL">All Categories</option>
            <option value="ONGOING">Ongoing Pipeline</option>
            <option value="APPROVED">Approved Projects</option>
            <option value="REVIEW">Under Review / Pending</option>
            <option value="HIGH_RISK">High / Critical Risk</option>
          </select>
        </div>
      </div>

      {/* Table Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-sm">Ingested Infrastructure Projects</h3>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-medium">
              {filtered.length} of {projects.length}
            </span>
          </div>
          <Link
            to="/dashboard/projects"
            className="text-xs font-semibold text-government-blue hover:text-blue-800 flex items-center gap-1"
          >
            Explore Complete Registry <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-500 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-government-blue" />
            <p className="text-sm font-medium">Loading newly onboarded projects...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-slate-500 px-4">
            <FileText className="w-12 h-12 mx-auto text-slate-300 mb-3" />
            <h4 className="text-base font-semibold text-slate-800">No projects found</h4>
            <p className="text-sm text-slate-500 max-w-md mx-auto mt-1 mb-5">
              {searchTerm || statusFilter !== 'ALL' 
                ? 'No projects match your search criteria. Try modifying your filters.'
                : 'No newly added projects were found in your authorized sector scope.'}
            </p>
            {canManageProjects && (
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-government-blue text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors"
              >
                <PlusCircle className="w-4 h-4" /> Register New Project
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider">
                    Project Identifier & Title
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider">
                    Ministry & Sector
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider">
                    Location & State
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider text-right">
                    Cost (₹ Cr)
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider text-center">
                    Progress
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider text-center">
                    Risk / Status
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider">
                    Created Details
                  </th>
                  <th className="px-6 py-3.5 font-semibold text-slate-700 text-xs uppercase tracking-wider text-right">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((proj) => {
                  const riskLevel = proj.overall_risk || 'LOW';
                  const riskColor = 
                    riskLevel === 'CRITICAL' ? 'bg-red-50 text-red-700 border-red-200' :
                    riskLevel === 'HIGH' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    riskLevel === 'MEDIUM' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                    'bg-slate-50 text-slate-700 border-slate-200';

                  const createdDate = proj.created_at 
                    ? new Date(proj.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                    : 'System Import';

                  return (
                    <tr key={proj.project_code} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-mono font-bold text-government-blue text-xs tracking-wide">
                          {proj.project_code}
                        </div>
                        <div className="text-slate-900 font-semibold mt-0.5 max-w-sm truncate" title={proj.project_name}>
                          {proj.project_name}
                        </div>
                        {proj.agency && (
                          <div className="text-xs text-slate-400 mt-0.5">
                            Agency: {proj.agency}
                          </div>
                        )}
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800 text-xs max-w-xs truncate" title={proj.ministry}>
                          {proj.ministry || 'N/A'}
                        </div>
                        <div className="inline-block mt-1 px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-medium">
                          {proj.sector || 'General'}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-xs">
                        <div className="font-medium text-slate-800">{proj.state || 'Pan-India'}</div>
                        <div className="text-slate-500 mt-0.5">
                          {proj.district || proj.location || 'Central Corridor'}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-right font-medium text-slate-900 text-xs">
                        <div>₹{(proj.revised_cost || proj.original_cost || 0).toLocaleString()}</div>
                        {proj.cumulative_expenditure ? (
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            Exp: ₹{proj.cumulative_expenditure.toLocaleString()}
                          </div>
                        ) : null}
                      </td>

                      <td className="px-6 py-4 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className="text-xs font-bold text-slate-800">
                            {Math.round(proj.physical_progress || 0)}%
                          </span>
                          <div className="w-16 bg-slate-200 rounded-full h-1.5 mt-1 overflow-hidden">
                            <div 
                              className="bg-government-blue h-1.5 rounded-full" 
                              style={{ width: `${Math.min(Math.max(proj.physical_progress || 0, 0), 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-center space-y-1">
                        <div>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${riskColor}`}>
                            {riskLevel}
                          </span>
                        </div>
                        <div>
                          <span className="inline-block text-[11px] text-slate-500 font-medium bg-slate-100 px-1.5 py-0.5 rounded">
                            {proj.status || 'Ongoing'}
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-600">
                        <div className="flex items-center gap-1 text-slate-700">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          <span>{createdDate}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5 truncate max-w-[140px]" title={proj.created_by}>
                          By: {proj.created_by || 'Admin'}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/dashboard/projects/${encodeURIComponent(proj.project_code)}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-government-blue bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
                        >
                          View Details <ArrowRight className="w-3 h-3 ml-0.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add New Project Modal */}
      <AddNewProjectModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={handleProjectCreated}
      />
    </div>
  );
};

export default NewProjectsView;
