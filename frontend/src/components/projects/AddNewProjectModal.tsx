import React, { useState, useEffect } from 'react';
import { 
  X, 
  Building2, 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  ShieldAlert
} from 'lucide-react';
import { projectApi } from '../../services/api';
import type { CreateProjectPayload, DuplicateCheckResult } from '../../services/api';

interface AddNewProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (projectCode: string) => void;
}

const INDIAN_STATES = [
  "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", 
  "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", 
  "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", 
  "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", 
  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", 
  "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", 
  "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Multi-State"
];

const COMMON_MINISTRIES = [
  "Ministry of Road Transport and Highways",
  "Ministry of Railways",
  "Ministry of Power",
  "Ministry of Petroleum and Natural Gas",
  "Ministry of Housing and Urban Affairs",
  "Ministry of Civil Aviation",
  "Ministry of Ports, Shipping and Waterways",
  "Ministry of Jal Shakti",
  "Ministry of Communications",
  "Ministry of Coal",
  "Ministry of Health and Family Welfare",
  "Ministry of Education",
  "Ministry of Steel",
  "Ministry of New and Renewable Energy"
];

export const AddNewProjectModal: React.FC<AddNewProjectModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [sectors, setSectors] = useState<string[]>([]);

  // Form fields
  const [projectId, setProjectId] = useState('');
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('Ongoing');

  const [ministry, setMinistry] = useState('');
  const [department, setDepartment] = useState('');
  const [agency, setAgency] = useState('');
  const [sector, setSector] = useState('');

  const [state, setState] = useState('');
  const [district, setDistrict] = useState('');
  const [location, setLocation] = useState('');

  const [approvalDate, setApprovalDate] = useState('');
  const [originalCompletionDate, setOriginalCompletionDate] = useState('');
  const [revisedCompletionDate, setRevisedCompletionDate] = useState('');

  const [originalCost, setOriginalCost] = useState('');
  const [revisedCost, setRevisedCost] = useState('');
  const [cumulativeExpenditure, setCumulativeExpenditure] = useState('');

  const [physicalProgress, setPhysicalProgress] = useState('');
  const [reportingMonth, setReportingMonth] = useState('April 2026');

  const [milestones, setMilestones] = useState('');
  const [remarks, setRemarks] = useState('');

  // Duplicate checking & submission state
  const [isCheckingDuplicate, setIsCheckingDuplicate] = useState(false);
  const [duplicateCheck, setDuplicateCheck] = useState<DuplicateCheckResult | null>(null);
  const [confirmSimilarDuplicate, setConfirmSimilarDuplicate] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      projectApi.getSectors()
        .then(({ data }) => setSectors(data))
        .catch(() => setSectors([
          'Aviation', 'Education', 'Health', 'Other', 'Petroleum & Gas',
          'Ports & Shipping', 'Power & Energy', 'Railways', 'Roads & Highways',
          'Steel', 'Telecom', 'Urban Development', 'Water Resources'
        ]));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Real-time blur duplicate check
  const handleCheckDuplicate = async () => {
    if (!projectId.trim()) return;
    setIsCheckingDuplicate(true);
    setDuplicateCheck(null);
    setConfirmSimilarDuplicate(false);
    try {
      const { data } = await projectApi.checkDuplicate(projectId.trim(), projectName.trim() || undefined);
      setDuplicateCheck(data);
    } catch {
      // ignore network check error
    } finally {
      setIsCheckingDuplicate(false);
    }
  };

  const validate = () => {
    const errors: Record<string, string> = {};

    if (!projectId.trim()) errors.projectId = 'Project ID is required.';
    if (!projectName.trim()) errors.projectName = 'Project Name is required.';
    if (!ministry.trim()) errors.ministry = 'Ministry is required.';
    if (!sector.trim()) errors.sector = 'Sector is required.';
    if (!state.trim()) errors.state = 'State / Region is required.';

    const origCostNum = parseFloat(originalCost);
    if (isNaN(origCostNum) || origCostNum < 0) {
      errors.originalCost = 'Original cost must be a non-negative number.';
    }

    if (revisedCost) {
      const revCostNum = parseFloat(revisedCost);
      if (isNaN(revCostNum) || revCostNum < 0) {
        errors.revisedCost = 'Revised cost must be non-negative.';
      }
    }

    if (cumulativeExpenditure) {
      const expNum = parseFloat(cumulativeExpenditure);
      if (isNaN(expNum) || expNum < 0) {
        errors.cumulativeExpenditure = 'Cumulative expenditure must be non-negative.';
      }
    }

    if (physicalProgress) {
      const progNum = parseFloat(physicalProgress);
      if (isNaN(progNum) || progNum < 0 || progNum > 100) {
        errors.physicalProgress = 'Physical progress must be between 0 and 100%.';
      }
    }

    if (approvalDate && originalCompletionDate) {
      if (new Date(originalCompletionDate) < new Date(approvalDate)) {
        errors.originalCompletionDate = 'Completion date cannot be earlier than approval date.';
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!validate()) return;

    if (duplicateCheck?.exists) {
      setErrorMessage('Cannot proceed: A project with this Project ID already exists.');
      return;
    }

    if (duplicateCheck?.possible_duplicate && !confirmSimilarDuplicate) {
      setErrorMessage('Please review the similar existing project notice and confirm before adding.');
      return;
    }

    setIsSubmitting(true);

    const payload: CreateProjectPayload = {
      project_code: projectId.trim(),
      project_name: projectName.trim(),
      ministry: ministry.trim(),
      department: department.trim() || undefined,
      agency: agency.trim() || undefined,
      sector: sector.trim(),
      state: state.trim(),
      district: district.trim() || undefined,
      location: location.trim() || undefined,
      approval_date: approvalDate || undefined,
      original_completion_date: originalCompletionDate || undefined,
      revised_completion_date: revisedCompletionDate || undefined,
      original_cost: parseFloat(originalCost),
      revised_cost: revisedCost ? parseFloat(revisedCost) : undefined,
      cumulative_expenditure: cumulativeExpenditure ? parseFloat(cumulativeExpenditure) : undefined,
      physical_progress: physicalProgress ? parseFloat(physicalProgress) : undefined,
      reporting_month: reportingMonth.trim() || undefined,
      status: status || 'Ongoing',
      remarks: remarks.trim() || undefined,
      milestones: milestones.trim() || undefined,
    };

    try {
      const { data } = await projectApi.create(payload);
      onSuccess(data.project_code);
      onClose();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Unable to create project. Please verify inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl my-8 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-government-blue text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-lg">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Register New Infrastructure Project</h2>
              <p className="text-xs text-blue-100">PAIMANA / MoSPI National Project-Monitoring Registry</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
          {errorMessage && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-800 text-sm">
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* SECTION 1 — PROJECT IDENTITY */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">1</span>
              Project Identity
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Project ID / Code <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    placeholder="e.g. 700145 or NH-2026-01"
                    value={projectId}
                    onChange={(e) => setProjectId(e.target.value)}
                    onBlur={handleCheckDuplicate}
                    className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue font-mono ${
                      fieldErrors.projectId ? 'border-red-500' : 'border-slate-300'
                    }`}
                  />
                  {isCheckingDuplicate && (
                    <Loader2 className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 animate-spin" />
                  )}
                </div>
                {fieldErrors.projectId && <p className="text-xs text-red-500 mt-1">{fieldErrors.projectId}</p>}
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Project Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Official project title as per approval document"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  onBlur={handleCheckDuplicate}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue ${
                    fieldErrors.projectName ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.projectName && <p className="text-xs text-red-500 mt-1">{fieldErrors.projectName}</p>}
              </div>
            </div>

            {/* Duplicate Notice Banner */}
            {duplicateCheck?.exists && (
              <div className="p-3 bg-red-100 border border-red-300 rounded-lg text-red-800 text-xs flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <strong>Project ID Collision:</strong> A project with ID <code>{duplicateCheck.existing_project?.project_code}</code> already exists ({duplicateCheck.existing_project?.project_name}). Project IDs must be unique.
                </div>
              </div>
            )}

            {duplicateCheck?.possible_duplicate && !duplicateCheck.exists && (
              <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 text-xs space-y-2">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <strong>Possible Duplicate Project Found:</strong>
                    <div className="mt-1 text-slate-700">
                      Matches existing project: <strong>{duplicateCheck.existing_project?.project_code}</strong> — {duplicateCheck.existing_project?.project_name} ({duplicateCheck.existing_project?.ministry || 'N/A'}, {duplicateCheck.existing_project?.state || 'N/A'}).
                    </div>
                  </div>
                </div>
                <label className="flex items-center gap-2 pt-1 font-semibold text-slate-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={confirmSimilarDuplicate}
                    onChange={(e) => setConfirmSimilarDuplicate(e.target.checked)}
                    className="rounded text-government-blue focus:ring-government-blue"
                  />
                  I confirm this is a distinct, legitimate infrastructure project
                </label>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Project Description / Scope
                </label>
                <input
                  type="text"
                  placeholder="Brief summary of engineering scope and alignment"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Project Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue bg-white"
                >
                  <option value="Ongoing">Ongoing</option>
                  <option value="Under Evaluation">Under Evaluation</option>
                  <option value="Pending Review">Pending Review</option>
                  <option value="Commissioned">Commissioned</option>
                </select>
              </div>
            </div>
          </div>

          {/* SECTION 2 — ORGANIZATION */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">2</span>
              Organization & Sector Scope
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Ministry <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  list="ministry-suggestions"
                  required
                  placeholder="e.g. Ministry of Railways"
                  value={ministry}
                  onChange={(e) => setMinistry(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue ${
                    fieldErrors.ministry ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                <datalist id="ministry-suggestions">
                  {COMMON_MINISTRIES.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
                {fieldErrors.ministry && <p className="text-xs text-red-500 mt-1">{fieldErrors.ministry}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Sector (Loaded from DB) <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue bg-white ${
                    fieldErrors.sector ? 'border-red-500' : 'border-slate-300'
                  }`}
                >
                  <option value="">-- Select DB Sector --</option>
                  {sectors.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                {fieldErrors.sector && <p className="text-xs text-red-500 mt-1">{fieldErrors.sector}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Department
                </label>
                <input
                  type="text"
                  placeholder="e.g. Railway Board, CPWD, NHAI RO"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Agency / Implementing Agency
                </label>
                <input
                  type="text"
                  placeholder="e.g. RVNL, NHAI, NTPC, AAI"
                  value={agency}
                  onChange={(e) => setAgency(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
            </div>
          </div>

          {/* SECTION 3 — LOCATION */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">3</span>
              Project Location
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  State / UT <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue bg-white ${
                    fieldErrors.state ? 'border-red-500' : 'border-slate-300'
                  }`}
                >
                  <option value="">-- Select State / UT --</option>
                  {INDIAN_STATES.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
                {fieldErrors.state && <p className="text-xs text-red-500 mt-1">{fieldErrors.state}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  District (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Pune, Gandhinagar"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Specific Site / Alignment
                </label>
                <input
                  type="text"
                  placeholder="e.g. Package III (KM 120-185)"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
            </div>
          </div>

          {/* SECTION 4 — PROJECT DATES */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">4</span>
              Project Timeline
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Date of Approval
                </label>
                <input
                  type="date"
                  value={approvalDate}
                  onChange={(e) => setApprovalDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Original Target Date of Completion
                </label>
                <input
                  type="date"
                  value={originalCompletionDate}
                  onChange={(e) => setOriginalCompletionDate(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue ${
                    fieldErrors.originalCompletionDate ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.originalCompletionDate && (
                  <p className="text-xs text-red-500 mt-1">{fieldErrors.originalCompletionDate}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Revised Date of Completion (Optional)
                </label>
                <input
                  type="date"
                  value={revisedCompletionDate}
                  onChange={(e) => setRevisedCompletionDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
            </div>
          </div>

          {/* SECTION 5 — FINANCIAL INFORMATION */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">5</span>
              Financial Information (₹ Crore)
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Original Approved Cost (₹ Cr) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="0.00"
                  value={originalCost}
                  onChange={(e) => setOriginalCost(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue font-mono ${
                    fieldErrors.originalCost ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.originalCost && <p className="text-xs text-red-500 mt-1">{fieldErrors.originalCost}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Revised Cost (₹ Cr, Optional)
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={revisedCost}
                  onChange={(e) => setRevisedCost(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue font-mono ${
                    fieldErrors.revisedCost ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.revisedCost && <p className="text-xs text-red-500 mt-1">{fieldErrors.revisedCost}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Cumulative Expenditure (₹ Cr)
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={cumulativeExpenditure}
                  onChange={(e) => setCumulativeExpenditure(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue font-mono ${
                    fieldErrors.cumulativeExpenditure ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.cumulativeExpenditure && (
                  <p className="text-xs text-red-500 mt-1">{fieldErrors.cumulativeExpenditure}</p>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 6 — CURRENT PROGRESS & INITIAL SNAPSHOT */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">6</span>
              Current Progress & Initial Monthly Snapshot
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Physical Progress (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="0 - 100"
                  value={physicalProgress}
                  onChange={(e) => setPhysicalProgress(e.target.value)}
                  className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue font-mono ${
                    fieldErrors.physicalProgress ? 'border-red-500' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.physicalProgress && (
                  <p className="text-xs text-red-500 mt-1">{fieldErrors.physicalProgress}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Reporting Month
                </label>
                <input
                  type="text"
                  placeholder="e.g. April 2026"
                  value={reportingMonth}
                  onChange={(e) => setReportingMonth(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
            </div>
          </div>

          {/* SECTION 7 — ADDITIONAL INFORMATION */}
          <div className="bg-slate-50/70 p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-government-blue font-bold text-sm border-b border-slate-200 pb-2">
              <span className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center text-xs">7</span>
              Milestones & Administrative Remarks
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Key Milestones Achieved / Targeted
                </label>
                <input
                  type="text"
                  placeholder="e.g. Land acquisition 90% completed; Utility shifting in progress"
                  value={milestones}
                  onChange={(e) => setMilestones(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Remarks / Inter-Departmental Issues
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Forest clearance awaiting state environmental committee review"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-government-blue"
                />
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || duplicateCheck?.exists}
              className="px-6 py-2.5 text-sm font-bold bg-government-blue hover:bg-blue-800 disabled:opacity-50 text-white rounded-xl shadow-md transition-all flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Registering Project...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" /> Validate & Register Project
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
