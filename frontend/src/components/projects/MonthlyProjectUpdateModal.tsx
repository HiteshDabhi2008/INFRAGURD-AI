import React, { useState, useEffect } from 'react';
import { 
  X, Search, AlertTriangle, CheckCircle, 
  ChevronRight, AlertCircle, Lock, Calendar
} from 'lucide-react';
import { projectApi } from '../../services/api';
import type { MonthlyUpdatePayload, MonthlyUpdateResponse, ProjectSummary } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface MonthlyProjectUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  initialProject?: ProjectSummary | null;
}

export const MonthlyProjectUpdateModal: React.FC<MonthlyProjectUpdateModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProject = null,
}) => {
  const { user } = useAuth();
  const isViewer = user?.role === 'Viewer / Auditor' || user?.authority_type === 'Viewer / Auditor';

  // Search & Project selection
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ProjectSummary[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null);

  // Form fields
  const [reportMonth, setReportMonth] = useState('August 2026');
  const [physicalProgress, setPhysicalProgress] = useState<string>('');
  const [cumulativeExpenditure, setCumulativeExpenditure] = useState<string>('');
  const [projectStatus, setProjectStatus] = useState('Ongoing');
  const [revisedCost, setRevisedCost] = useState<string>('');
  const [revisedCompletionDate, setRevisedCompletionDate] = useState<string>('');
  const [remarks, setRemarks] = useState('');

  // Duplicate detection & edit mode
  const [existingSnapshot, setExistingSnapshot] = useState<any>(null);
  const [allowEdit, setAllowEdit] = useState(false);
  const [viewingExisting, setViewingExisting] = useState(false);
  const [conflictWarning, setConflictWarning] = useState<string | null>(null);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<MonthlyUpdateResponse | null>(null);

  useEffect(() => {
    if (initialProject) {
      setSelectedProject(initialProject);
      if (initialProject.revised_cost) setRevisedCost(String(initialProject.revised_cost));
      if (initialProject.physical_progress !== undefined) setPhysicalProgress(String(initialProject.physical_progress));
      if (initialProject.cumulative_expenditure !== undefined) setCumulativeExpenditure(String(initialProject.cumulative_expenditure));
    } else {
      setSelectedProject(null);
      resetForm();
    }
  }, [initialProject, isOpen]);

  // Check for existing snapshot whenever project or month changes
  useEffect(() => {
    if (selectedProject && reportMonth.trim()) {
      checkExistingMonth(selectedProject.project_code, reportMonth.trim());
    } else {
      setExistingSnapshot(null);
      setConflictWarning(null);
    }
  }, [selectedProject, reportMonth]);

  const checkExistingMonth = async (code: string, month: string) => {
    try {
      const res = await projectApi.getSnapshot(code, month);
      if (res.data.exists && res.data.snapshot) {
        setExistingSnapshot(res.data.snapshot);
        setConflictWarning(`A snapshot for "${month}" is already recorded in the database.`);
      } else {
        setExistingSnapshot(null);
        setConflictWarning(null);
        setAllowEdit(false);
        setViewingExisting(false);
      }
    } catch {
      // Ignore network errors on silent check
    }
  };

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (val.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await projectApi.search(val.trim());
      setSearchResults(res.data);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const selectProject = (p: ProjectSummary) => {
    setSelectedProject(p);
    setSearchResults([]);
    setSearchQuery('');
    if (p.revised_cost) setRevisedCost(String(p.revised_cost));
    if (p.physical_progress !== undefined) setPhysicalProgress(String(p.physical_progress));
    if (p.cumulative_expenditure !== undefined) setCumulativeExpenditure(String(p.cumulative_expenditure));
  };

  const resetForm = () => {
    setReportMonth('August 2026');
    setPhysicalProgress('');
    setCumulativeExpenditure('');
    setProjectStatus('Ongoing');
    setRevisedCost('');
    setRevisedCompletionDate('');
    setRemarks('');
    setExistingSnapshot(null);
    setAllowEdit(false);
    setViewingExisting(false);
    setConflictWarning(null);
    setErrorMsg(null);
    setSuccessData(null);
  };

  const handleEditExisting = () => {
    if (existingSnapshot) {
      setAllowEdit(true);
      setViewingExisting(false);
      if (existingSnapshot.physical_progress !== undefined && existingSnapshot.physical_progress !== null) {
        setPhysicalProgress(String(existingSnapshot.physical_progress));
      }
      if (existingSnapshot.cumulative_expenditure !== undefined && existingSnapshot.cumulative_expenditure !== null) {
        setCumulativeExpenditure(String(existingSnapshot.cumulative_expenditure));
      }
      if (existingSnapshot.project_status) setProjectStatus(existingSnapshot.project_status);
      if (existingSnapshot.revised_cost) setRevisedCost(String(existingSnapshot.revised_cost));
      if (existingSnapshot.revised_completion_date) setRevisedCompletionDate(existingSnapshot.revised_completion_date);
      if (existingSnapshot.remarks) setRemarks(existingSnapshot.remarks);
      setConflictWarning(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) {
      setErrorMsg('Please select a project first.');
      return;
    }
    if (!reportMonth.trim()) {
      setErrorMsg('Reporting month is required.');
      return;
    }
    const prog = parseFloat(physicalProgress);
    if (isNaN(prog) || prog < 0 || prog > 100) {
      setErrorMsg('Physical progress must be a valid number between 0% and 100%.');
      return;
    }
    const exp = parseFloat(cumulativeExpenditure);
    if (isNaN(exp) || exp < 0) {
      setErrorMsg('Cumulative expenditure must be a non-negative number.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    const payload: MonthlyUpdatePayload = {
      report_month: reportMonth.trim(),
      physical_progress: prog,
      cumulative_expenditure: exp,
      project_status: projectStatus,
      revised_cost: revisedCost ? parseFloat(revisedCost) : undefined,
      revised_completion_date: revisedCompletionDate || undefined,
      remarks: remarks.trim() || undefined,
      allow_edit: allowEdit,
    };

    try {
      const response = await projectApi.monthlyUpdate(selectedProject.project_code, payload);
      setSuccessData(response.data);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      if (err.response?.status === 409) {
        const data = err.response.data;
        setExistingSnapshot(data.existing_snapshot);
        setConflictWarning(data.detail || 'A snapshot for this month already exists.');
      } else {
        setErrorMsg(err.response?.data?.detail || 'Failed to submit monthly update. Please check values.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-gradient-to-r from-government-blue to-blue-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Monthly Project Data Entry</h2>
              <p className="text-xs text-blue-200">
                MoSPI / IPMD Non-Destructive Snapshot & ML Risk Engine Re-evaluation
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 max-h-[80vh] overflow-y-auto">
          {successData ? (
            <div className="py-6 text-center space-y-6">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle className="w-10 h-10" />
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-bold text-slate-900">Monthly Update Successfully Saved!</h3>
                <p className="text-sm text-slate-600 max-w-md mx-auto">
                  Snapshot for <strong className="text-slate-900">{successData.snapshot.report_month}</strong> recorded.
                  AI Risk Engine and M3/M4 models have re-evaluated the project metrics in real time.
                </p>
              </div>

              {/* Real-time ML Evaluation Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left p-4 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
                  <div className="text-xs text-slate-500 font-medium">Updated Risk Score</div>
                  <div className="text-2xl font-black text-slate-900 mt-1 flex items-baseline gap-2">
                    {successData.risk_assessment.risk_score}
                    <span className="text-xs font-semibold text-slate-400">/ 100</span>
                  </div>
                  <span className={`inline-block mt-1 text-[11px] font-bold px-2 py-0.5 rounded ${
                    successData.risk_assessment.overall_risk === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                    successData.risk_assessment.overall_risk === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                    successData.risk_assessment.overall_risk === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    {successData.risk_assessment.overall_risk} RISK
                  </span>
                </div>

                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
                  <div className="text-xs text-slate-500 font-medium">M3 Cost Overrun</div>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {successData.predictions.predicted_cost_overrun.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Risk Level: <strong className="text-slate-800">{successData.predictions.cost_risk_level}</strong>
                  </div>
                </div>

                <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
                  <div className="text-xs text-slate-500 font-medium">M4 Time Overrun</div>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {successData.predictions.predicted_time_months.toFixed(1)} <span className="text-sm font-normal text-slate-500">mo</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Delay Risk: <strong className="text-slate-800">{successData.predictions.time_risk_level}</strong>
                  </div>
                </div>
              </div>

              {successData.risk_assessment.warnings?.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-left">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-800 uppercase tracking-wider mb-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Early Warnings Triggered
                  </div>
                  <ul className="text-xs text-amber-900 space-y-1 list-disc list-inside">
                    {successData.risk_assessment.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex justify-center gap-3 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => {
                    setSuccessData(null);
                    resetForm();
                  }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-semibold transition-colors"
                >
                  Add Another Month
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 bg-government-blue hover:bg-blue-800 text-white rounded-lg text-sm font-semibold shadow-md transition-colors"
                >
                  Done & Close
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {isViewer && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-3 text-xs text-amber-800">
                  <Lock className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    <strong>Read-Only Notice:</strong> Your account has Viewer / Auditor permissions. You can inspect project data, but monthly update submissions are restricted to authorized ministry and agency officers.
                  </span>
                </div>
              )}

              {/* 1. Project Selection / Autocomplete */}
              {!initialProject && (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Select Infrastructure Project <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue focus:border-transparent transition-all"
                      placeholder="Search by Project Code, Name, or Agency..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                    />
                    {searching && (
                      <div className="absolute right-3 top-3 text-xs text-slate-400 font-medium">Searching...</div>
                    )}
                    {searchResults.length > 0 && (
                      <div className="absolute z-30 left-0 right-0 top-11 bg-white border border-slate-200 rounded-xl shadow-xl max-h-56 overflow-y-auto divide-y divide-slate-100">
                        {searchResults.map((p) => (
                          <button
                            key={p.project_code}
                            type="button"
                            onClick={() => selectProject(p)}
                            className="w-full text-left p-3 hover:bg-blue-50 transition-colors flex items-center justify-between group"
                          >
                            <div className="space-y-0.5">
                              <div className="text-sm font-bold text-slate-900 group-hover:text-blue-700">
                                {p.project_code}
                              </div>
                              <div className="text-xs text-slate-600 line-clamp-1">{p.project_name}</div>
                              <div className="text-[11px] text-slate-400">
                                {p.agency || 'Agency'} • {p.state || 'State'}
                              </div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Selected Project Metadata Card */}
              {selectedProject && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-government-blue bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {selectedProject.project_code}
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 mt-1">{selectedProject.project_name}</h4>
                    </div>
                    {!initialProject && (
                      <button
                        type="button"
                        onClick={() => setSelectedProject(null)}
                        className="text-xs text-red-600 hover:text-red-700 font-medium underline"
                      >
                        Change
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-2 border-t border-slate-200">
                    <div>
                      <span className="text-slate-500 block">Agency:</span>
                      <span className="font-semibold text-slate-800">{selectedProject.agency || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">State:</span>
                      <span className="font-semibold text-slate-800">{selectedProject.state || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Original Cost:</span>
                      <span className="font-semibold text-slate-800">
                        ₹{selectedProject.original_cost?.toLocaleString() || 0} Cr
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Current Progress:</span>
                      <span className="font-semibold text-slate-800">
                        {selectedProject.physical_progress !== undefined ? `${selectedProject.physical_progress}%` : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Duplicate Month Alert Banner */}
              {conflictWarning && (
                <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-xl space-y-3">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-bold text-amber-900">Snapshot Already Exists</h4>
                      <p className="text-xs text-amber-700 mt-0.5">{conflictWarning}</p>
                      {existingSnapshot?.created_by && (
                        <p className="text-[11px] text-amber-600 mt-1">
                          Recorded by: <strong>{existingSnapshot.created_by}</strong> on{' '}
                          {new Date(existingSnapshot.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setViewingExisting(!viewingExisting)}
                      className="px-3 py-1.5 bg-white border border-amber-300 text-amber-800 hover:bg-amber-100 rounded-md text-xs font-semibold shadow-xs transition-colors"
                    >
                      {viewingExisting ? 'Hide Existing Data' : 'View Existing Data'}
                    </button>
                    <button
                      type="button"
                      onClick={handleEditExisting}
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors"
                    >
                      Edit Existing Data
                    </button>
                  </div>

                  {viewingExisting && existingSnapshot && (
                    <div className="p-3 bg-white rounded-lg border border-amber-200 text-xs space-y-2 mt-2">
                      <div className="font-bold text-slate-800">Current Recorded Values:</div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <div>
                          <span className="text-slate-500 block">Progress:</span>
                          <span className="font-semibold text-slate-900">{existingSnapshot.physical_progress}%</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Expenditure:</span>
                          <span className="font-semibold text-slate-900">₹{existingSnapshot.cumulative_expenditure} Cr</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Status:</span>
                          <span className="font-semibold text-slate-900">{existingSnapshot.project_status || 'Ongoing'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Revised Cost:</span>
                          <span className="font-semibold text-slate-900">₹{existingSnapshot.revised_cost || 'N/A'} Cr</span>
                        </div>
                      </div>
                      {existingSnapshot.remarks && (
                        <div className="pt-1 border-t border-slate-100">
                          <span className="text-slate-500 block">Remarks:</span>
                          <span className="text-slate-700">{existingSnapshot.remarks}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {allowEdit && (
                <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between text-xs text-blue-900">
                  <span className="font-medium">
                    ✏️ <strong>Edit Mode Active:</strong> You are updating the existing snapshot for {reportMonth}.
                  </span>
                  <button
                    type="button"
                    onClick={() => setAllowEdit(false)}
                    className="text-xs text-blue-700 hover:underline font-semibold"
                  >
                    Cancel Edit Mode
                  </button>
                </div>
              )}

              {/* Data Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Reporting Month */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Reporting Month <span className="text-red-500">*</span>
                  </label>
                  <div className="space-y-1.5">
                    <input
                      type="text"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                      placeholder="e.g. August 2026, September 2026"
                      value={reportMonth}
                      onChange={(e) => setReportMonth(e.target.value)}
                      required
                    />
                    <div className="flex gap-1.5">
                      {['August 2026', 'September 2026', 'October 2026'].map((m) => (
                        <button
                          key={m}
                          type="button"
                          onClick={() => setReportMonth(m)}
                          className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${
                            reportMonth === m
                              ? 'bg-blue-100 border-blue-300 text-blue-800 font-semibold'
                              : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Project Status */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Project Status <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                    value={projectStatus}
                    onChange={(e) => setProjectStatus(e.target.value)}
                  >
                    <option value="Ongoing">Ongoing</option>
                    <option value="On Schedule">On Schedule</option>
                    <option value="Ahead of Schedule">Ahead of Schedule</option>
                    <option value="Delayed">Delayed</option>
                    <option value="Critical">Critical</option>
                    <option value="Under Review">Under Review</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>

                {/* Physical Progress (%) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Physical Progress (%) <span className="text-red-500">*</span></span>
                    {physicalProgress && !isNaN(parseFloat(physicalProgress)) && (
                      <span className="text-slate-500 font-mono text-[11px]">{parseFloat(physicalProgress)}%</span>
                    )}
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                    placeholder="0.0 - 100.0"
                    value={physicalProgress}
                    onChange={(e) => setPhysicalProgress(e.target.value)}
                    required
                  />
                  {/* Progress Bar Preview */}
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-300"
                      style={{ width: `${Math.min(Math.max(parseFloat(physicalProgress) || 0, 0), 100)}%` }}
                    />
                  </div>
                </div>

                {/* Cumulative Expenditure (₹ Cr) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Cumulative Expenditure (₹ Cr) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                    placeholder="Amount spent up to reporting month"
                    value={cumulativeExpenditure}
                    onChange={(e) => setCumulativeExpenditure(e.target.value)}
                    required
                  />
                  {selectedProject?.original_cost && cumulativeExpenditure && (
                    <div className="text-[11px] text-slate-500 mt-1">
                      Utilization:{' '}
                      <strong>
                        {((parseFloat(cumulativeExpenditure) / (selectedProject.revised_cost || selectedProject.original_cost)) * 100).toFixed(1)}%
                      </strong>{' '}
                      of sanction
                    </div>
                  )}
                </div>

                {/* Revised Cost (Optional) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Revised Sanctioned Cost (₹ Cr, Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                    placeholder="Leave blank if unchanged"
                    value={revisedCost}
                    onChange={(e) => setRevisedCost(e.target.value)}
                  />
                </div>

                {/* Revised Completion Date (Optional) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Revised Completion Date (Optional)
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                    value={revisedCompletionDate}
                    onChange={(e) => setRevisedCompletionDate(e.target.value)}
                  />
                </div>
              </div>

              {/* Remarks */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  MoSPI / Agency Official Remarks (Optional)
                </label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-government-blue"
                  placeholder="Record progress notes, site milestones, land acquisition updates, or bottlenecks..."
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                />
              </div>

              {/* Error Banner */}
              {errorMsg && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || isViewer || !selectedProject}
                  className="px-6 py-2 bg-government-blue hover:bg-blue-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg shadow-md hover:shadow-lg transition-all flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Saving & Re-evaluating ML Models...</span>
                    </>
                  ) : allowEdit ? (
                    <span>Update Existing Snapshot</span>
                  ) : (
                    <span>Submit Monthly Update</span>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
