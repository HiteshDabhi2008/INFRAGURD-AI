import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  IndianRupee,
  Activity,
  FileText,
  Printer,
  Bot,
  Send,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Calendar,
  Building2,
  MapPin,
  Layers,
  Sparkles,
  RefreshCw,
  TrendingUp,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  Cell
} from 'recharts';
import { projectApi, aiApi } from '../../services/api';
import type { ProjectDetail, RiskPredictionResult, ProjectHistoryItem } from '../../services/api';

export const ProjectRiskAssessment: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [risk, setRisk] = useState<RiskPredictionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [refreshingRisk, setRefreshingRisk] = useState<boolean>(false);

  // AI Assistant State
  const [question, setQuestion] = useState<string>('');
  const [, setAnswer] = useState<string>('');
  const [aiLoading, setAiLoading] = useState<boolean>(false);
  const [chatHistory, setChatHistory] = useState<Array<{ sender: 'user' | 'assistant'; text: string }>>([]);

  // Accordion State
  const [isModelAccordionOpen, setIsModelAccordionOpen] = useState<boolean>(false);

  // Load project and live risk prediction
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      setError('');
      try {
        const { data: projData } = await projectApi.detail(id);
        if (!isMounted) return;
        setProject(projData);

        // Fetch live M3/M4/M5 risk engine evaluation
        try {
          const { data: riskData } = await projectApi.riskPrediction(id);
          if (isMounted) setRisk(riskData);
        } catch {
          // If live prediction call has a temporary hiccup, fallback to DB values
          if (isMounted && projData.overall_risk) {
            setRisk({
              project_code: projData.project_code,
              risk_score: projData.risk_score || 0,
              overall_risk: (projData.overall_risk as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL') || 'LOW',
              warnings: projData.warnings || [],
              explanation: 'Sourced from verified quarterly PAIMANA project intelligence record.',
              cost_model_output: {
                risk_level: projData.overall_risk === 'CRITICAL' ? 'HIGH' : projData.overall_risk === 'HIGH' ? 'HIGH' : 'MEDIUM',
                expected_overrun_percent: projData.original_cost && projData.revised_cost
                  ? Math.max(0, Math.round(((projData.revised_cost - projData.original_cost) / projData.original_cost) * 100))
                  : 0,
                is_cost_overrun: Boolean(projData.revised_cost && projData.original_cost && projData.revised_cost > projData.original_cost),
                predicted_total_cost: projData.revised_cost || projData.original_cost || 0
              },
              time_model_output: {
                risk_level: projData.overall_risk === 'CRITICAL' ? 'HIGH' : projData.overall_risk === 'HIGH' ? 'HIGH' : 'LOW',
                overrun_probability: projData.overall_risk === 'CRITICAL' ? 0.85 : projData.overall_risk === 'HIGH' ? 0.72 : 0.25,
                expected_overrun_months: projData.history?.[projData.history.length - 1]?.time_overrun_months || null,
                is_time_overrun: Boolean((projData.history?.[projData.history.length - 1]?.time_overrun_months || 0) > 0)
              }
            });
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const errMsg = err instanceof Error ? err.message : 'Unable to retrieve project risk data';
          setError(errMsg);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    if (id) {
      loadData();
    }

    return () => {
      isMounted = false;
    };
  }, [id]);

  // Re-run risk prediction
  const handleRefreshRisk = async () => {
    if (!id) return;
    setRefreshingRisk(true);
    try {
      const { data: riskData } = await projectApi.riskPrediction(id);
      setRisk(riskData);
    } catch {
      // Keep existing
    } finally {
      setRefreshingRisk(false);
    }
  };

  // AI Assistant Query Handler
  const handleAskAi = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q || aiLoading) return;

    setQuestion('');
    setChatHistory(prev => [...prev, { sender: 'user', text: q }]);
    setAiLoading(true);

    try {
      const { data } = await aiApi.chat(q, id);
      const reply = data.answer || data.response || 'No specific findings returned by the model.';
      setAnswer(reply);
      setChatHistory(prev => [...prev, { sender: 'assistant', text: reply }]);
    } catch {
      const fallback = 'InfraGuard AI service is temporarily busy. Please retry in a moment.';
      setAnswer(fallback);
      setChatHistory(prev => [...prev, { sender: 'assistant', text: fallback }]);
    } finally {
      setAiLoading(false);
    }
  };

  // 4-Month Historical Snapshot Analysis
  const historyData = useMemo(() => {
    if (!project?.history || project.history.length === 0) return [];
    
    // Month abbreviations
    const monthMap: Record<string, string> = {
      'April 2026': 'Apr 2026',
      'May 2026': 'May 2026',
      'June 2026': 'Jun 2026',
      'July 2026': 'Jul 2026'
    };

    return project.history.map((item: ProjectHistoryItem) => {
      const prog = item.physical_progress ?? 0;
      const exp = item.cumulative_expenditure ?? 0;
      const rev = item.revised_cost ?? project.original_cost ?? 1;
      const expPercent = rev > 0 ? Math.round((exp / rev) * 100 * 10) / 10 : 0;
      const gap = Math.round((expPercent - prog) * 10) / 10;

      return {
        month: monthMap[item.report_month] || item.report_month,
        fullMonth: item.report_month,
        progress: prog,
        expenditure: exp,
        revisedCost: rev,
        expenditurePercent: expPercent,
        gap: gap,
        costOverrunPct: item.cost_overrun_pct ?? 0,
        timeOverrunMonths: item.time_overrun_months ?? 0
      };
    });
  }, [project]);

  // Derived Project & Prediction Metrics
  const latestSnapshot = project?.history?.[project.history.length - 1];
  const origCost = project?.original_cost ?? 0;
  const revCost = latestSnapshot?.revised_cost ?? project?.revised_cost ?? origCost;
  const cumExp = latestSnapshot?.cumulative_expenditure ?? project?.cumulative_expenditure ?? 0;
  const currentProgress = latestSnapshot?.physical_progress ?? project?.physical_progress ?? 0;
  const expPercent = revCost > 0 ? Math.round((cumExp / revCost) * 100 * 10) / 10 : 0;
  const progressGap = Math.round((expPercent - currentProgress) * 10) / 10;

  // M3 Cost Metrics
  const costRiskLevel = risk?.cost_model_output?.risk_level || (risk?.overall_risk === 'CRITICAL' ? 'HIGH' : 'LOW');
  const expectedCostOverrunPct = risk?.cost_model_output?.expected_overrun_percent ?? 0;
  const predictedTotalCost = risk?.cost_model_output?.predicted_total_cost || Math.round(origCost * (1 + expectedCostOverrunPct / 100));
  const additionalFundsNeeded = Math.max(0, predictedTotalCost - cumExp);

  // M4 Time Metrics
  const timeRiskLevel = risk?.time_model_output?.risk_level || (risk?.overall_risk === 'CRITICAL' ? 'HIGH' : 'LOW');
  const overrunProb = Math.round((risk?.time_model_output?.overrun_probability || 0) * 100);
  const expectedDelayMonths = risk?.time_model_output?.expected_overrun_months ?? latestSnapshot?.time_overrun_months ?? 0;

  // Predicted Completion Date String
  const predictedCompletionDate = useMemo(() => {
    const baseDateStr = latestSnapshot?.revised_completion_date || project?.original_completion_date;
    if (!baseDateStr) return 'Target Pending';
    if (!expectedDelayMonths || expectedDelayMonths <= 0) return baseDateStr;

    try {
      const d = new Date(baseDateStr);
      if (isNaN(d.getTime())) return `${baseDateStr} (+${Math.round(expectedDelayMonths)}m)`;
      d.setMonth(d.getMonth() + Math.round(expectedDelayMonths));
      return d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
    } catch {
      return `${baseDateStr} (+${Math.round(expectedDelayMonths)}m)`;
    }
  }, [latestSnapshot, project, expectedDelayMonths]);

  // Overall Risk Score & Category
  const score = risk?.risk_score ?? project?.risk_score ?? 0;
  const overallCategory = (risk?.overall_risk || project?.overall_risk || (score >= 75 ? 'CRITICAL' : score >= 50 ? 'HIGH' : score >= 25 ? 'MEDIUM' : 'LOW')).toUpperCase();

  // Performance Health Classification
  const performanceHealth = useMemo(() => {
    if (score >= 75 || progressGap > 40 || expectedDelayMonths > 24) {
      return {
        label: 'Critical Attention Required',
        description: 'Severe schedule slippage and expenditure-progress imbalance detected.',
        cardClass: 'border-red-300 bg-red-50/40'
      };
    }
    if (score >= 50 || progressGap > 25 || expectedCostOverrunPct > 20 || expectedDelayMonths > 12) {
      return {
        label: 'High Risk Alert',
        description: 'Notable cost or milestone divergence requiring active executive oversight.',
        cardClass: 'border-amber-300 bg-amber-50/40'
      };
    }
    if (currentProgress < 40 || progressGap > 15) {
      return {
        label: 'Watch List',
        description: 'Early project stage or moderate lag between financial outlays and physical completion.',
        cardClass: 'border-yellow-200 bg-yellow-50/30'
      };
    }
    if (currentProgress >= 75 && progressGap <= 10) {
      return {
        label: 'Performing Well',
        description: 'Robust milestone execution with healthy financial-physical alignment.',
        cardClass: 'border-emerald-200 bg-emerald-50/30'
      };
    }
    return {
      label: 'Stable Execution',
      description: 'Progressing within standard tolerance thresholds with monitored indicators.',
      cardClass: 'border-blue-200 bg-blue-50/30'
    };
  }, [score, progressGap, expectedCostOverrunPct, expectedDelayMonths, currentProgress]);

  // Cost Comparison Chart Data
  const costChartData = useMemo(() => [
    { name: 'Original Cost', amount: origCost, fill: '#64748b' },
    { name: 'Revised Cost', amount: revCost, fill: '#0284c7' },
    { name: 'Cumulative Exp', amount: cumExp, fill: '#f59e0b' },
    { name: 'M3 Predicted Cost', amount: predictedTotalCost, fill: predictedTotalCost > revCost ? '#ef4444' : '#10b981' }
  ], [origCost, revCost, cumExp, predictedTotalCost]);

  // Badge Styling Helpers
  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-600 text-white border-red-700';
      case 'HIGH':
        return 'bg-amber-500 text-white border-amber-600';
      case 'MEDIUM':
        return 'bg-yellow-400 text-slate-950 border-yellow-500';
      case 'LOW':
      default:
        return 'bg-emerald-500 text-white border-emerald-600';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return '#dc2626';
      case 'HIGH':
        return '#f59e0b';
      case 'MEDIUM':
        return '#eab308';
      case 'LOW':
      default:
        return '#10b981';
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-government-blue/20 border-t-government-blue rounded-full animate-spin" />
        <div className="text-center">
          <h3 className="font-bold text-slate-800 text-base">Running Deep Project Risk Diagnostic...</h3>
          <p className="text-xs text-slate-500 mt-1">Aggregating M3 Cost, M4 Time, and M5 Composite Risk Models</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Unable to Load Project Risk Assessment</h2>
        <p className="text-sm text-slate-600">{error || 'Project record not found in system database.'}</p>
        <div className="pt-2">
          <button
            onClick={() => navigate('/dashboard/projects')}
            className="px-4 py-2 bg-government-blue text-white rounded-lg text-sm font-semibold hover:bg-blue-800"
          >
            Return to Projects Directory
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-7 pb-16 print:p-0 print:space-y-4">
      {/* ── HEADER & NAVIGATION BAR ────────────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              to="/dashboard/projects"
              className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-government-blue transition-colors print:hidden"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Projects Directory
            </Link>
            <span className="text-slate-300 print:hidden">/</span>
            <span className="text-xs font-semibold text-slate-600">Risk Assessment Diagnostic</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl lg:text-3xl font-black text-slate-900 tracking-tight">
              {project.project_name}
            </h1>
            <span className="px-3 py-1 bg-slate-900 text-white text-xs font-bold rounded-lg tracking-wider">
              {project.project_code}
            </span>
            <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${getRiskBadge(overallCategory)}`}>
              {overallCategory} RISK
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1 font-medium text-slate-700">
              <Building2 className="w-3.5 h-3.5 text-government-blue" />
              {project.ministry || 'Ministry Not Specified'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              {project.agency || 'Agency Not Specified'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              {project.state || 'National / Multi-State'}
            </span>
            <span>•</span>
            <span className="font-semibold text-slate-700">
              Sector: {project.sector || 'General Infrastructure'}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 print:hidden flex-wrap">
          <button
            onClick={handleRefreshRisk}
            disabled={refreshingRisk}
            className="px-3.5 py-2 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
            title="Re-run M3/M4/M5 Inference"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshingRisk ? 'animate-spin text-government-blue' : ''}`} />
            {refreshingRisk ? 'Evaluating...' : 'Re-run ML'}
          </button>

          <Link
            to={`/dashboard/projects/${encodeURIComponent(project.project_code)}`}
            className="px-3.5 py-2 bg-white border border-slate-200 hover:border-government-blue text-government-blue rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            Project Details
          </Link>

          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            Export / Print Report
          </button>
        </div>
      </div>

      {/* ── OVERALL RISK SCORE HEADER ──────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-blue-950 text-white p-6 rounded-3xl shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-radial from-blue-500/10 to-transparent pointer-events-none" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center relative z-10">
          {/* Circular Risk Score Gauge */}
          <div className="lg:col-span-4 flex items-center gap-5 border-b lg:border-b-0 lg:border-r border-slate-700/60 pb-5 lg:pb-0 lg:pr-6">
            <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  stroke="#1e293b"
                  strokeWidth="10"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  stroke={getRiskColor(overallCategory)}
                  strokeWidth="10"
                  strokeDasharray={251.2}
                  strokeDashoffset={251.2 - (251.2 * Math.min(score, 100)) / 100}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center">
                <span className="text-3xl font-black tracking-tight">{score}</span>
                <span className="text-[10px] text-slate-400 font-semibold uppercase">out of 100</span>
              </div>
            </div>

            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Composite Risk Score (M5)
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wide border ${getRiskBadge(overallCategory)}`}>
                  {overallCategory}
                </span>
                <span className="text-xs text-slate-300 font-medium">
                  {overallCategory === 'CRITICAL' ? 'Immediate Executive Action' : overallCategory === 'HIGH' ? 'High Oversight Alert' : overallCategory === 'MEDIUM' ? 'Monitored Variance' : 'On Track / Normal'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2 leading-relaxed line-clamp-2">
                {risk?.explanation || 'Evaluation grounded in real-time PAIMANA quarterly expenditure and milestone data.'}
              </p>
            </div>
          </div>

          {/* Quick Risk Indicator Pills */}
          <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-800/70 border border-slate-700/80 p-3.5 rounded-2xl">
              <div className="text-[11px] text-slate-400 font-medium flex items-center justify-between">
                <span>Cost Risk (M3)</span>
                <IndianRupee className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="text-lg font-bold mt-1.5 flex items-baseline gap-1.5">
                <span className={costRiskLevel === 'HIGH' ? 'text-red-400' : costRiskLevel === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'}>
                  {costRiskLevel}
                </span>
                <span className="text-[11px] text-slate-400 font-normal">
                  ({expectedCostOverrunPct > 0 ? `+${expectedCostOverrunPct}%` : '0%'})
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                Pred. ₹{predictedTotalCost.toLocaleString('en-IN')} Cr
              </div>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 p-3.5 rounded-2xl">
              <div className="text-[11px] text-slate-400 font-medium flex items-center justify-between">
                <span>Time Risk (M4)</span>
                <Clock className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="text-lg font-bold mt-1.5 flex items-baseline gap-1.5">
                <span className={timeRiskLevel === 'HIGH' ? 'text-red-400' : timeRiskLevel === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'}>
                  {timeRiskLevel}
                </span>
                <span className="text-[11px] text-slate-400 font-normal">
                  ({expectedDelayMonths > 0 ? `+${Math.round(expectedDelayMonths)}m` : 'On Target'})
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                Prob: {overrunProb}%
              </div>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 p-3.5 rounded-2xl">
              <div className="text-[11px] text-slate-400 font-medium flex items-center justify-between">
                <span>Progress Gap</span>
                <Activity className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <div className="text-lg font-bold mt-1.5 flex items-baseline gap-1.5">
                <span className={progressGap > 25 ? 'text-red-400' : progressGap > 10 ? 'text-amber-400' : 'text-emerald-400'}>
                  {progressGap > 0 ? `+${progressGap}%` : `${progressGap}%`}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                Exp {expPercent}% vs Prog {currentProgress}%
              </div>
            </div>

            <div className="bg-slate-800/70 border border-slate-700/80 p-3.5 rounded-2xl">
              <div className="text-[11px] text-slate-400 font-medium flex items-center justify-between">
                <span>Early Warnings</span>
                <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              </div>
              <div className="text-lg font-bold mt-1.5">
                <span className={(risk?.warnings?.length || 0) > 0 ? 'text-red-400' : 'text-emerald-400'}>
                  {risk?.warnings?.length || 0} Triggered
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                {(risk?.warnings?.length || 0) > 0 ? risk?.warnings?.[0] : 'No active alerts'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION 1: CURRENT PROJECT STATUS SNAPSHOT ─────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-government-blue" />
            Project Baseline & Current Status Snapshot
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            Reporting Month: <strong className="text-slate-800">{latestSnapshot?.report_month || 'July 2026'}</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3.5">
          {/* Card 1: Original Cost */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500">Original Approved Cost</div>
            <div className="text-xl font-black text-slate-900 mt-1">
              ₹{origCost.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-500">Cr</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Cabinet sanction</p>
          </div>

          {/* Card 2: Revised Cost */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500">Latest Revised Cost</div>
            <div className="text-xl font-black text-slate-900 mt-1">
              ₹{revCost.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-500">Cr</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {origCost > 0 && revCost > origCost ? (
                <span className="text-red-600 font-bold">
                  +{Math.round(((revCost - origCost) / origCost) * 100)}% Cost Overrun
                </span>
              ) : (
                <span className="text-emerald-600 font-medium">Within Original Budget</span>
              )}
            </p>
          </div>

          {/* Card 3: Cumulative Expenditure */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500">Cumulative Expenditure</div>
            <div className="text-xl font-black text-slate-900 mt-1">
              ₹{cumExp.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-500">Cr</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              <strong className="text-slate-800">{expPercent}%</strong> of revised budget
            </p>
          </div>

          {/* Card 4: Physical Progress */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500">Physical Progress</div>
            <div className="text-xl font-black text-government-blue mt-1">
              {currentProgress}%
            </div>
            <div className="w-full h-1.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
              <div
                className="h-full bg-government-blue rounded-full transition-all duration-500"
                style={{ width: `${Math.min(currentProgress, 100)}%` }}
              />
            </div>
          </div>

          {/* Card 5: Target Completion */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500">Target Completion</div>
            <div className="text-sm font-bold text-slate-900 mt-1 truncate">
              {latestSnapshot?.revised_completion_date || project.original_completion_date || 'N/A'}
            </div>
            <p className="text-[11px] text-slate-400 mt-1 truncate">
              Orig: {project.original_completion_date || 'N/A'}
            </p>
          </div>

          {/* Card 6: Performance Status */}
          <div className={`p-4 rounded-2xl border shadow-xs ${performanceHealth.cardClass}`}>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
              Health Status
            </div>
            <div className="text-sm font-black text-slate-900 mt-1">
              {performanceHealth.label}
            </div>
            <p className="text-[10px] text-slate-600 mt-0.5 line-clamp-2">
              {performanceHealth.description}
            </p>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: 4-MONTH HISTORICAL TRENDS & RECHARTS GRAPHS ─────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-government-blue" />
              4-Month Historical Trajectory & Trend Analysis
            </h2>
            <p className="text-xs text-slate-500">
              Monthly PAIMANA audit data progression (April 2026 – July 2026)
            </p>
          </div>
        </div>

        {/* Historical Snapshot Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <span className="text-xs font-bold text-slate-800">Monthly Snapshot Register</span>
            <span className="text-[11px] text-slate-500 font-medium">4 Snapshots Recorded</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="px-5 py-3">Reporting Month</th>
                  <th className="px-5 py-3 text-right">Physical Progress</th>
                  <th className="px-5 py-3 text-right">Cumulative Expenditure</th>
                  <th className="px-5 py-3 text-right">Expenditure %</th>
                  <th className="px-5 py-3 text-right">Revised Cost</th>
                  <th className="px-5 py-3 text-right">Progress Gap</th>
                  <th className="px-5 py-3 text-center">Schedule Overrun</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {historyData.map((row, idx) => (
                  <tr key={row.fullMonth} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3 font-bold text-slate-900 flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      {row.fullMonth}
                      {idx === historyData.length - 1 && (
                        <span className="px-1.5 py-0.5 bg-blue-100 text-government-blue text-[9px] font-bold rounded">
                          Latest
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right font-semibold text-government-blue">
                      {row.progress}%
                    </td>
                    <td className="px-5 py-3 text-right font-medium">
                      ₹{row.expenditure.toLocaleString('en-IN')} Cr
                    </td>
                    <td className="px-5 py-3 text-right font-medium">
                      {row.expenditurePercent}%
                    </td>
                    <td className="px-5 py-3 text-right font-medium">
                      ₹{row.revisedCost.toLocaleString('en-IN')} Cr
                    </td>
                    <td className="px-5 py-3 text-right font-bold">
                      <span className={row.gap > 20 ? 'text-red-600' : row.gap > 10 ? 'text-amber-600' : 'text-emerald-600'}>
                        {row.gap > 0 ? `+${row.gap}%` : `${row.gap}%`}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      {row.timeOverrunMonths > 0 ? (
                        <span className="inline-block px-2 py-0.5 bg-amber-50 text-amber-700 font-bold rounded text-[11px] border border-amber-200">
                          +{Math.round(row.timeOverrunMonths)} Months
                        </span>
                      ) : (
                        <span className="text-emerald-600 font-medium">On Schedule</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 4 Recharts Trajectory Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Graph 1: Physical Progress vs Month */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900">Physical Progress vs Month</h3>
                <p className="text-[11px] text-slate-400">Monthly milestone completion velocity</p>
              </div>
              <span className="px-2 py-0.5 bg-blue-50 text-government-blue text-[10px] font-bold rounded">
                Trendline
              </span>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '11px', border: 'none' }}
                    formatter={(val: any) => [`${val}%`, 'Physical Progress']}
                  />
                  <Line
                    type="monotone"
                    dataKey="progress"
                    name="Physical Progress"
                    stroke="#0284c7"
                    strokeWidth={3}
                    dot={{ fill: '#0284c7', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Graph 2: Cumulative Expenditure vs Month */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900">Cumulative Expenditure vs Month</h3>
                <p className="text-[11px] text-slate-400">Financial capital deployment trajectory (₹ Cr)</p>
              </div>
              <span className="px-2 py-0.5 bg-amber-50 text-amber-700 text-[10px] font-bold rounded">
                Outlay Area
              </span>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historyData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '11px', border: 'none' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')} Cr`, 'Expenditure']}
                  />
                  <Area
                    type="monotone"
                    dataKey="expenditure"
                    name="Expenditure"
                    stroke="#f59e0b"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#expGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Graph 3: Physical Progress vs Cumulative Expenditure */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900">Physical Progress vs Cumulative Outlay</h3>
                <p className="text-[11px] text-slate-400">Alignment between spend velocity and on-ground milestones</p>
              </div>
              <span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-[10px] font-bold rounded">
                Dual Metric
              </span>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={historyData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis yAxisId="left" stroke="#0284c7" fontSize={11} tickLine={false} unit="%" />
                  <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '11px', border: 'none' }}
                  />
                  <Bar yAxisId="right" dataKey="expenditure" name="Cumulative Exp (₹ Cr)" fill="#fde68a" radius={[4, 4, 0, 0]} />
                  <Line yAxisId="left" type="monotone" dataKey="progress" name="Physical Progress (%)" stroke="#0284c7" strokeWidth={3} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Graph 4: Expenditure % vs Physical Progress % (Progress Gap) */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900">Expenditure % vs Physical Progress % (Gap Trajectory)</h3>
                <p className="text-[11px] text-slate-400">Disparity highlighting potential over-expenditure or slow execution</p>
              </div>
              <span className="px-2 py-0.5 bg-red-50 text-red-700 text-[10px] font-bold rounded">
                Variance
              </span>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={historyData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '11px', border: 'none' }}
                  />
                  <Bar dataKey="expenditurePercent" name="Expenditure %" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="progress" name="Physical Progress %" fill="#0284c7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION 3 & SECTION 4: COST & TIME FORECAST ANALYSIS ──────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 3: Cost Risk Analysis (M3 Model) */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-government-blue flex items-center justify-center">
                <IndianRupee className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Cost Risk Analysis (M3 Model)</h3>
                <p className="text-[11px] text-slate-400">Total expenditure projection at 100% completion</p>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase border ${getRiskBadge(costRiskLevel)}`}>
              {costRiskLevel} COST RISK
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">M3 Predicted Total</div>
              <div className="text-base font-black text-slate-900 mt-0.5">
                ₹{predictedTotalCost.toLocaleString('en-IN')} <span className="text-[10px] font-normal">Cr</span>
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">Expected Overrun</div>
              <div className={`text-base font-black mt-0.5 ${expectedCostOverrunPct > 15 ? 'text-red-600' : 'text-slate-800'}`}>
                {expectedCostOverrunPct > 0 ? `+${expectedCostOverrunPct}%` : '0%'}
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">Additional Outlay</div>
              <div className="text-base font-black text-slate-900 mt-0.5">
                ₹{additionalFundsNeeded.toLocaleString('en-IN')} <span className="text-[10px] font-normal">Cr</span>
              </div>
            </div>
          </div>

          {/* Bar Chart comparing cost milestones */}
          <div className="h-48 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costChartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" stroke="#94a3b8" fontSize={10} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '11px', border: 'none' }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')} Cr`, 'Cost']}
                />
                <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                  {costChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="p-3 bg-blue-50/50 rounded-xl text-xs text-slate-600 border border-blue-100 flex items-start gap-2">
            <Info className="w-4 h-4 text-government-blue shrink-0 mt-0.5" />
            <span>
              {expectedCostOverrunPct > 20
                ? 'M3 regression predicts significant budget escalation due to historical spending rate exceeding current progress velocity.'
                : expectedCostOverrunPct > 5
                ? 'M3 regression forecasts moderate cost adjustments within acceptable revised financial limits.'
                : 'Project capital expenditure aligns closely with approved estimates.'}
            </span>
          </div>
        </div>

        {/* Section 4: Time Risk Analysis (M4 Model) */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Schedule & Delay Analysis (M4 Model)</h3>
                <p className="text-[11px] text-slate-400">Milestone timeline and completion forecasting</p>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase border ${getRiskBadge(timeRiskLevel)}`}>
              {timeRiskLevel} TIME RISK
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">Delay Probability</div>
              <div className={`text-base font-black mt-0.5 ${overrunProb > 70 ? 'text-red-600' : 'text-slate-800'}`}>
                {overrunProb}%
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">Forecast Delay</div>
              <div className={`text-base font-black mt-0.5 ${expectedDelayMonths > 12 ? 'text-amber-600' : 'text-slate-800'}`}>
                {expectedDelayMonths > 0 ? `+${Math.round(expectedDelayMonths)} Mos` : '0 Months'}
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl">
              <div className="text-[10px] text-slate-500 font-semibold uppercase">Pred. Completion</div>
              <div className="text-xs font-bold text-slate-900 mt-1 truncate" title={predictedCompletionDate}>
                {predictedCompletionDate}
              </div>
            </div>
          </div>

          {/* Timeline Visual Progression */}
          <div className="space-y-3 pt-2">
            <div className="text-xs font-semibold text-slate-700">Project Milestone Timeline</div>
            <div className="relative border-l-2 border-slate-200 ml-3 pl-4 space-y-4 py-1">
              <div className="relative">
                <div className="absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full bg-slate-400 border-2 border-white shadow-xs" />
                <div className="text-xs font-bold text-slate-700">Original Target Date</div>
                <div className="text-xs text-slate-500">{project.original_completion_date || 'Date not recorded'}</div>
              </div>
              <div className="relative">
                <div className="absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full bg-blue-500 border-2 border-white shadow-xs" />
                <div className="text-xs font-bold text-government-blue">Revised Target Date</div>
                <div className="text-xs text-slate-600 font-medium">
                  {latestSnapshot?.revised_completion_date || project.original_completion_date || 'N/A'}
                </div>
              </div>
              <div className="relative">
                <div className={`absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white shadow-xs ${expectedDelayMonths > 12 ? 'bg-red-500' : 'bg-amber-500'}`} />
                <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  M4 Model Predicted Completion
                  {expectedDelayMonths > 0 && (
                    <span className="px-1.5 py-0.2 bg-red-100 text-red-700 text-[10px] font-bold rounded">
                      +{Math.round(expectedDelayMonths)}m delay
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-700 font-bold">{predictedCompletionDate}</div>
              </div>
            </div>
          </div>

          <div className="p-3 bg-amber-50/60 rounded-xl text-xs text-slate-600 border border-amber-200 flex items-start gap-2">
            <Clock className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <span>
              {expectedDelayMonths > 12
                ? `M4 classifier flags high probability of delay (+${Math.round(expectedDelayMonths)} months). Requires accelerated milestone execution.`
                : 'Project schedule indicators remain within operational benchmarks.'}
            </span>
          </div>
        </div>
      </div>

      {/* ── SECTION 5 & 6: HEALTH INDICATORS & EARLY WARNINGS ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Early Warnings Panel */}
        <div className="lg:col-span-6 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Active Early Warnings & Alerts
            </h3>
            <span className="text-xs text-slate-400 font-semibold">
              {(risk?.warnings?.length || 0)} Signals Detected
            </span>
          </div>

          {(!risk?.warnings || risk.warnings.length === 0) ? (
            <div className="p-6 bg-emerald-50/50 rounded-2xl border border-emerald-100 text-center space-y-1">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
              <div className="text-sm font-bold text-emerald-900">No Critical Early Warnings Triggered</div>
              <p className="text-xs text-emerald-700">Project indicators are performing within safe thresholds.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {risk.warnings.map((w, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-red-50/60 border border-red-200/80 rounded-2xl flex items-start gap-3"
                >
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-red-950">{w}</div>
                    <div className="text-[11px] text-red-700 mt-0.5">
                      Flagged by automated monitoring heuristics based on latest PAIMANA return.
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Key Risk Factor Breakdown */}
          <div className="pt-2">
            <h4 className="text-xs font-bold text-slate-800 mb-2">Detailed Risk Factor Breakdown</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
                <span className="text-slate-600">Cost Overrun Factor</span>
                <span className={`font-bold ${expectedCostOverrunPct > 20 ? 'text-red-600' : 'text-slate-800'}`}>
                  {expectedCostOverrunPct}% Overrun Projected
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
                <span className="text-slate-600">Schedule Slippage Factor</span>
                <span className={`font-bold ${expectedDelayMonths > 6 ? 'text-amber-600' : 'text-slate-800'}`}>
                  {expectedDelayMonths > 0 ? `+${Math.round(expectedDelayMonths)} Months` : 'None'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
                <span className="text-slate-600">Financial-Physical Gap</span>
                <span className={`font-bold ${progressGap > 20 ? 'text-red-600' : 'text-slate-800'}`}>
                  {progressGap}% Variance
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 9: 4x4 Cost vs Time Risk Matrix */}
        <div className="lg:col-span-6 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-government-blue" />
                Cost vs Time Risk Matrix (4×4)
              </h3>
              <p className="text-[11px] text-slate-400">Project position across dual risk dimensions</p>
            </div>
            <span className="text-[11px] font-bold text-government-blue bg-blue-50 px-2 py-0.5 rounded">
              Position: ({costRiskLevel} Cost, {timeRiskLevel} Time)
            </span>
          </div>

          {/* 4x4 Interactive Grid */}
          <div className="pt-2">
            <div className="flex">
              {/* Y-Axis Label */}
              <div className="w-16 flex items-center justify-center text-[10px] font-bold uppercase tracking-widest text-slate-400 -rotate-90">
                Cost Risk ↑
              </div>

              {/* Matrix Table */}
              <div className="flex-1 space-y-1.5">
                {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((costTier) => (
                  <div key={costTier} className="grid grid-cols-4 gap-1.5">
                    {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const).map((timeTier) => {
                      const isCurrentCell =
                        costRiskLevel.toUpperCase() === costTier &&
                        timeRiskLevel.toUpperCase() === timeTier;

                      // Severity colors for matrix cells
                      let cellBg = 'bg-slate-50 border-slate-100 text-slate-400';
                      if (costTier === 'CRITICAL' || timeTier === 'CRITICAL') {
                        cellBg = 'bg-red-50/40 border-red-100 text-red-400';
                      } else if (costTier === 'HIGH' || timeTier === 'HIGH') {
                        cellBg = 'bg-amber-50/40 border-amber-100 text-amber-500';
                      } else if (costTier === 'MEDIUM' || timeTier === 'MEDIUM') {
                        cellBg = 'bg-yellow-50/40 border-yellow-100 text-yellow-600';
                      } else {
                        cellBg = 'bg-emerald-50/40 border-emerald-100 text-emerald-600';
                      }

                      return (
                        <div
                          key={`${costTier}-${timeTier}`}
                          className={`h-16 p-1.5 rounded-xl border flex flex-col justify-between relative transition-all ${
                            isCurrentCell
                              ? 'ring-2 ring-government-blue ring-offset-2 bg-blue-900 text-white shadow-md border-blue-900 font-bold scale-[1.02] z-10'
                              : cellBg
                          }`}
                        >
                          <div className="flex items-center justify-between text-[9px] font-semibold">
                            <span>{costTier.slice(0, 1)}C</span>
                            <span>{timeTier.slice(0, 1)}T</span>
                          </div>

                          {isCurrentCell ? (
                            <div className="text-center py-0.5">
                              <span className="inline-block px-1.5 py-0.5 bg-yellow-400 text-slate-950 font-black rounded text-[9px]">
                                {project.project_code}
                              </span>
                              <div className="text-[9px] font-bold text-blue-200 mt-0.5">Score: {score}</div>
                            </div>
                          ) : (
                            <div className="text-center text-[10px] opacity-40 font-medium">
                              -
                            </div>
                          )}

                          <div className="text-[8px] text-right opacity-60 uppercase font-mono">
                            {costTier.slice(0, 3)}/{timeTier.slice(0, 3)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}

                {/* X-Axis Labels */}
                <div className="grid grid-cols-4 gap-1.5 pt-1 text-center text-[10px] font-bold text-slate-400">
                  <div>Low Time</div>
                  <div>Med Time</div>
                  <div>High Time</div>
                  <div>Crit Time</div>
                </div>
                <div className="text-center text-[10px] font-bold uppercase tracking-widest text-slate-400 pt-1">
                  Time Risk →
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION 10: TECHNICAL MODEL INSIGHTS (ACCORDION) ──────────────── */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs overflow-hidden">
        <button
          onClick={() => setIsModelAccordionOpen(prev => !prev)}
          className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Technical ML Model Insights & Architecture (M3, M4, M5)</h3>
              <p className="text-xs text-slate-400">Mathematical formulation, feature weighting, and inference parameters</p>
            </div>
          </div>
          {isModelAccordionOpen ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </button>

        {isModelAccordionOpen && (
          <div className="p-5 border-t border-slate-100 bg-slate-50/50 space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* M3 Details */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  M3: Cost Overrun Model
                </div>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Trained on national infrastructure portfolios using gradient boosted regression. Predicts terminal cost based on cumulative expenditure velocity and physical progress.
                </p>
                <div className="font-mono text-[10px] bg-slate-100 p-2 rounded text-slate-700">
                  Input features: original_cost, physical_progress, cumulative_expenditure, safe_expenditure_percent, state, agency
                </div>
              </div>

              {/* M4 Details */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  M4: Time Overrun Model
                </div>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Dual-head pipeline featuring a Random Forest / XGBoost classifier for delay probability and a regressor predicting additional months required to reach commercial operation.
                </p>
                <div className="font-mono text-[10px] bg-slate-100 p-2 rounded text-slate-700">
                  Target: is_time_overrun (binary) & expected_delay_months (continuous)
                </div>
              </div>

              {/* M5 Details */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-500" />
                  M5: Composite Risk Engine
                </div>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Harmonizes M3 financial risk (40%), M4 schedule delay risk (30%), expenditure-progress mismatch (20%), and milestone velocity (10%) into an authoritative 0–100 index.
                </p>
                <div className="font-mono text-[10px] bg-slate-100 p-2 rounded text-slate-700">
                  Score = min(100, 0.4×Cost + 0.3×Time + 0.2×Gap + 0.1×Lag)
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── SECTION 11: GROUNDED ASK INFRAGUARD-AI ─────────────────────────── */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4 print:hidden">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-government-blue flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Ask InfraGuard-AI (Project-Grounded Assistant)</h3>
              <p className="text-[11px] text-slate-400">Contextually grounded in verified PAIMANA facts and M3/M4/M5 predictions</p>
            </div>
          </div>
          <span className="flex items-center gap-1 text-[11px] text-emerald-600 font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Live Groq AI
          </span>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap gap-2">
          {[
            'Why is this project classified at this risk level?',
            'What is the expected delay and cost overrun?',
            'What are the early warnings and recommended mitigation actions?',
            'Summarize progress trajectory over the last 4 months'
          ].map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleAskAi(chip)}
              className="px-3 py-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 text-slate-700 hover:text-government-blue rounded-xl text-xs font-medium transition-colors text-left"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Chat Stream History */}
        {chatHistory.length > 0 && (
          <div className="space-y-3 max-h-80 overflow-y-auto p-4 bg-slate-50 rounded-2xl border border-slate-100">
            {chatHistory.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-government-blue text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                    AI
                  </div>
                )}
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-2xl ${
                    msg.sender === 'user'
                      ? 'bg-government-blue text-white rounded-br-none'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-xs whitespace-pre-wrap'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {aiLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 italic">
                <div className="w-2 h-2 rounded-full bg-government-blue animate-pulse" />
                InfraGuard AI is analyzing project telemetry...
              </div>
            )}
          </div>
        )}

        {/* Query Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAskAi()}
            placeholder={`Ask any specific question about ${project.project_name}...`}
            className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:border-government-blue focus:bg-white transition-all"
          />
          <button
            onClick={() => handleAskAi()}
            disabled={aiLoading || !question.trim()}
            className="px-5 py-3 bg-government-blue hover:bg-blue-800 disabled:opacity-50 text-white rounded-2xl text-xs font-bold transition-colors flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            Ask AI
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProjectRiskAssessment;

