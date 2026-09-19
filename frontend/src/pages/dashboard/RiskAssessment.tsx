import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  FolderKanban, 
  Bell, 
  Calendar, 
  ArrowUpRight, 
  ArrowDownRight, 
  ChevronDown, 
  ExternalLink, 
  Bot, 
  Send, 
  Sparkles, 
  TrendingUp, 
  Activity, 
  RefreshCw,
  X,
  ShieldAlert
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
} from 'recharts';
import { Link, useNavigate } from 'react-router-dom';
import { analyticsApi, aiApi } from '../../services/api';
import type { RiskDashboardData } from '../../services/api';

const RiskAssessment: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<RiskDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [selectedMinistry, setSelectedMinistry] = useState<string>('All Ministries');
  const [selectedSector, setSelectedSector] = useState<string>('All Sectors');
  const [selectedRiskFilter, setSelectedRiskFilter] = useState<string | null>(null);

  // AI Assistant State
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [aiSources, setAiSources] = useState<string[]>([]);

  const fetchDashboard = (ministry?: string, sector?: string) => {
    setLoading(true);
    setError('');
    const m = ministry && ministry !== 'All Ministries' ? ministry : undefined;
    const s = sector && sector !== 'All Sectors' ? sector : undefined;
    
    analyticsApi.riskDashboard({ ministry: m, sector: s })
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load risk dashboard:', err);
        setError('Unable to load risk assessment data. Please check backend connection.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDashboard(selectedMinistry, selectedSector);
  }, [selectedMinistry, selectedSector]);

  const handleAiAsk = async (prompt?: string) => {
    const query = prompt || aiQuestion;
    if (!query.trim() || aiLoading) return;
    
    setAiLoading(true);
    setAiResponse(null);
    setAiSources([]);
    try {
      const res = await aiApi.chat(query);
      setAiResponse(res.data.response || res.data.answer || 'Analysis complete.');
      setAiSources(res.data.sources || ['Project Database', 'M3 Cost Prediction', 'M4 Time Prediction', 'M5 Risk Engine']);
    } catch (err: any) {
      console.error('AI error:', err);
      setAiResponse('Unable to retrieve AI analysis at this moment. Please verify Groq API key.');
    } finally {
      setAiLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-government-blue mb-4" />
        <p className="font-semibold text-lg">Loading Risk Intelligence Dashboard...</p>
        <p className="text-sm text-slate-400">Processing PAIMANA project data, ML models & early warnings</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-8 text-center bg-red-50 rounded-xl border border-red-200 text-red-700 max-w-xl mx-auto my-12">
        <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-red-600" />
        <h3 className="font-bold text-lg mb-1">Failed to Load Risk Dashboard</h3>
        <p className="text-sm mb-4">{error}</p>
        <button 
          onClick={() => fetchDashboard(selectedMinistry, selectedSector)}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  if (!data) return null;

  // Filter projects if user clicked a donut slice or table filter
  const filteredProjects = selectedRiskFilter 
    ? data.high_risk_projects.filter(p => p.risk_level.toUpperCase() === selectedRiskFilter.toUpperCase())
    : data.high_risk_projects;

  return (
    <div className="space-y-6 pb-12 font-sans text-slate-900">
      
      {/* ── 1. HEADER SECTION ────────────────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-2xl font-bold text-slate-950 tracking-tight flex items-center gap-2.5">
            Risk Assessment Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Monitor project risks, identify critical issues and support timely action.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Last Updated Badge */}
          <div className="flex items-center gap-2 px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-600">
            <Calendar className="w-4 h-4 text-government-blue" />
            <span>Last Updated: <strong className="text-slate-800">{data.last_updated}</strong></span>
          </div>

          {/* Ministry Filter */}
          <div className="relative">
            <select
              value={selectedMinistry}
              onChange={(e) => setSelectedMinistry(e.target.value)}
              className="appearance-none bg-white pl-3.5 pr-9 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 hover:border-government-blue focus:ring-2 focus:ring-government-blue focus:outline-none cursor-pointer shadow-xs"
            >
              <option value="All Ministries">All Ministries</option>
              {data.ministries.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Sector Filter */}
          <div className="relative">
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="appearance-none bg-white pl-3.5 pr-9 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 hover:border-government-blue focus:ring-2 focus:ring-government-blue focus:outline-none cursor-pointer shadow-xs"
            >
              <option value="All Sectors">All Sectors</option>
              {data.sectors.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* ── 2. TOP 5 KPI CARDS ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        
        {/* Card 1: High Risk */}
        <div 
          onClick={() => setSelectedRiskFilter(selectedRiskFilter === 'HIGH' ? null : 'HIGH')}
          className={`bg-white p-4 rounded-2xl border transition-all cursor-pointer shadow-xs hover:shadow-md ${
            selectedRiskFilter === 'HIGH' ? 'border-red-500 ring-2 ring-red-100' : 'border-slate-200/80 hover:border-red-300'
          }`}
        >
          <div className="flex items-center gap-3 mb-2.5">
            <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-slate-600">High Risk Projects</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <div className="text-3xl font-black text-slate-900 tracking-tight">{data.kpis.high_risk}</div>
            <div className="flex items-center text-xs font-bold text-red-600">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              <span>{data.kpis.high_risk_mom}</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">from last month</p>
        </div>

        {/* Card 2: Medium Risk */}
        <div 
          onClick={() => setSelectedRiskFilter(selectedRiskFilter === 'MEDIUM' ? null : 'MEDIUM')}
          className={`bg-white p-4 rounded-2xl border transition-all cursor-pointer shadow-xs hover:shadow-md ${
            selectedRiskFilter === 'MEDIUM' ? 'border-amber-500 ring-2 ring-amber-100' : 'border-slate-200/80 hover:border-amber-300'
          }`}
        >
          <div className="flex items-center gap-3 mb-2.5">
            <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Medium Risk Projects</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <div className="text-3xl font-black text-slate-900 tracking-tight">{data.kpis.medium_risk}</div>
            <div className="flex items-center text-xs font-bold text-amber-600">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              <span>{data.kpis.medium_risk_mom}</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">from last month</p>
        </div>

        {/* Card 3: Low Risk */}
        <div 
          onClick={() => setSelectedRiskFilter(selectedRiskFilter === 'LOW' ? null : 'LOW')}
          className={`bg-white p-4 rounded-2xl border transition-all cursor-pointer shadow-xs hover:shadow-md ${
            selectedRiskFilter === 'LOW' ? 'border-emerald-500 ring-2 ring-emerald-100' : 'border-slate-200/80 hover:border-emerald-300'
          }`}
        >
          <div className="flex items-center gap-3 mb-2.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Low Risk Projects</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <div className="text-3xl font-black text-slate-900 tracking-tight">{data.kpis.low_risk}</div>
            <div className="flex items-center text-xs font-bold text-emerald-600">
              <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
              <span>{data.kpis.low_risk_mom}</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">from last month</p>
        </div>

        {/* Card 4: Total Projects */}
        <div 
          onClick={() => setSelectedRiskFilter(null)}
          className="bg-white p-4 rounded-2xl border border-slate-200/80 hover:border-blue-300 transition-all cursor-pointer shadow-xs hover:shadow-md"
        >
          <div className="flex items-center gap-3 mb-2.5">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-government-blue">
              <FolderKanban className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Total Projects Monitored</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <div className="text-3xl font-black text-slate-900 tracking-tight">{data.kpis.total_projects}</div>
            <div className="flex items-center text-xs font-bold text-blue-600">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              <span>+4</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">from last month</p>
        </div>

        {/* Card 5: Projects with Early Warning */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 hover:border-purple-300 transition-all shadow-xs hover:shadow-md">
          <div className="flex items-center gap-3 mb-2.5">
            <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
              <Bell className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Projects with Early Warning</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <div className="text-3xl font-black text-slate-900 tracking-tight">{data.kpis.early_warnings_count}</div>
            <div className="flex items-center text-xs font-bold text-purple-600">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              <span>{data.kpis.early_warnings_mom}</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">from last month</p>
        </div>

      </div>

      {/* ── 3. SECOND ROW (3 CHARTS: Distribution, Trend, Performance Overview) ──── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Chart 1: Risk Distribution Donut */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-900 text-sm">Risk Distribution</h3>
            {selectedRiskFilter && (
              <button 
                onClick={() => setSelectedRiskFilter(null)}
                className="text-[11px] text-government-blue font-semibold hover:underline flex items-center gap-1"
              >
                Clear filter <X className="w-3 h-3" />
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 items-center gap-2 py-2">
            {/* Donut Chart with total inside */}
            <div className="sm:col-span-7 h-48 relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.distribution}
                    dataKey="count"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    onClick={(entry: any) => {
                      const key = entry?.key ? String(entry.key) : null;
                      setSelectedRiskFilter(prev => prev === key ? null : key);
                    }}
                    className="cursor-pointer"
                  >
                    {data.distribution.map((entry) => (
                      <Cell 
                        key={`dist-${entry.key}`} 
                        fill={entry.color} 
                        stroke={selectedRiskFilter === entry.key ? '#0f172a' : '#fff'}
                        strokeWidth={selectedRiskFilter === entry.key ? 2 : 1}
                      />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    formatter={(val: any, name: any) => [`${val} projects`, name]}
                    contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              {/* Donut Center */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xl font-black text-slate-900 leading-tight">{data.kpis.total_projects}</span>
                <span className="text-[10px] text-slate-400 font-medium">Total Projects</span>
              </div>
            </div>

            {/* Donut Side Legend */}
            <div className="sm:col-span-5 space-y-2 text-xs">
              {data.distribution.map((item) => (
                <div 
                  key={item.key}
                  onClick={() => setSelectedRiskFilter(selectedRiskFilter === item.key ? null : item.key)}
                  className={`flex items-center justify-between p-1.5 rounded-lg transition-colors cursor-pointer ${
                    selectedRiskFilter === item.key ? 'bg-slate-100 font-bold' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-700">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-slate-900 mr-1.5">{item.count}</span>
                    <span className="text-[11px] text-slate-400">({item.percent}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 flex justify-between">
            <span>Click slice to filter table</span>
            <span className="text-emerald-600 font-semibold">{data.distribution.find(d => d.key === 'LOW')?.percent || 0}% Low Risk</span>
          </div>
        </div>

        {/* Chart 2: Risk Trend Line Chart */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-900 text-sm">Risk Trend (Historical Months)</h3>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1 text-red-600 font-medium">
                <span className="w-2 h-2 rounded-full bg-red-500" /> High
              </span>
              <span className="flex items-center gap-1 text-amber-600 font-medium">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> Medium
              </span>
              <span className="flex items-center gap-1 text-emerald-600 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Low
              </span>
            </div>
          </div>

          <div className="h-48 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.trend} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e2e8f0' }}
                />
                <Line type="monotone" dataKey="High" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 3, fill: '#ef4444' }} />
                <Line type="monotone" dataKey="Medium" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 3, fill: '#f59e0b' }} />
                <Line type="monotone" dataKey="Low" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3, fill: '#10b981' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 flex justify-between">
            <span>Source: 4-month PAIMANA snapshots</span>
            <span className="text-slate-600 font-medium">Updated July 2026</span>
          </div>
        </div>

        {/* Chart 3: Risk Performance Overview (REPLACING THE MAP!) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-bold text-slate-900 text-sm">Risk Performance Overview</h3>
              <span className="text-[10px] uppercase tracking-wider font-bold text-government-blue bg-blue-50 px-2 py-0.5 rounded">
                Portfolio Tiers
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Project distribution by delivery health and risk severity
            </p>

            <div className="space-y-3">
              {data.performance.map((tier) => {
                const isGood = tier.category.includes('Performing');
                const isStable = tier.category.includes('Stable');
                const isWatch = tier.category.includes('Watch');
                const isHigh = tier.category.includes('High');
                const barColor = isGood ? 'bg-emerald-500' : isStable ? 'bg-blue-500' : isWatch ? 'bg-amber-500' : isHigh ? 'bg-orange-500' : 'bg-red-600';
                
                return (
                  <div key={tier.category} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-700 truncate max-w-[200px]">{tier.category}</span>
                      <span className="font-bold text-slate-900">{tier.count} <span className="text-[11px] font-normal text-slate-400">({tier.percent}%)</span></span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${Math.min(tier.percent, 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-3 border-t border-slate-100 flex justify-between items-center">
            <span>Replaces geographic visualization</span>
            <span className="text-government-blue font-semibold">100% Data-Driven</span>
          </div>
        </div>

      </div>

      {/* ── 4. MAIN PROJECT ANALYSIS ROW (High Risk Projects & Risk Heatmap) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: High Risk Projects Table (8 cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden flex flex-col justify-between">
          <div>
            <div className="p-4 border-b border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <h3 className="font-bold text-slate-900 text-sm">
                  {selectedRiskFilter ? `${selectedRiskFilter} Risk Projects` : 'High Risk Projects'}
                </h3>
                <span className="text-xs font-semibold bg-red-50 text-red-700 px-2 py-0.5 rounded-full">
                  {filteredProjects.length} Identified
                </span>
              </div>

              {selectedRiskFilter && (
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500">Filtered by: <strong>{selectedRiskFilter}</strong></span>
                  <button 
                    onClick={() => setSelectedRiskFilter(null)}
                    className="text-red-600 hover:underline font-semibold flex items-center gap-0.5"
                  >
                    Clear <X className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
                  <tr>
                    <th className="px-4 py-3">Project ID</th>
                    <th className="px-4 py-3">Project Name</th>
                    <th className="px-4 py-3">Ministry / State</th>
                    <th className="px-4 py-3 text-center">Risk Level</th>
                    <th className="px-4 py-3 text-center">Cost Overrun</th>
                    <th className="px-4 py-3 text-center">Time Overrun</th>
                    <th className="px-4 py-3 text-center">Overall Risk</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredProjects.slice(0, 7).map((p) => {
                    const isCritical = p.risk_level === 'CRITICAL';
                    const isHigh = p.risk_level === 'HIGH';
                    const isMed = p.risk_level === 'MEDIUM';
                    
                    const badgeBg = isCritical ? 'bg-red-600 text-white' : isHigh ? 'bg-red-50 text-red-700 border border-red-200' : isMed ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200';
                    
                    return (
                      <tr key={p.project_code} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-4 py-3 font-bold text-government-blue">
                          {p.project_code}
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-800 max-w-[200px] truncate" title={p.project_name}>
                          {p.project_name}
                        </td>
                        <td className="px-4 py-3 text-slate-600 max-w-[130px] truncate" title={`${p.ministry} (${p.state})`}>
                          <div>{p.ministry.replace('Ministry of ', '')}</div>
                          <div className="text-[10px] text-slate-400">{p.state}</div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${badgeBg}`}>
                            {p.risk_level}
                          </span>
                        </td>
                        {/* Cost Overrun Risk Bar + % */}
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1.5">
                            <span className="text-[11px] font-bold text-red-600">{p.cost_overrun_pct}%</span>
                            <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-red-500 rounded-full" style={{ width: `${Math.min(p.cost_probability, 100)}%` }} />
                            </div>
                            <span className="text-[10px] text-slate-400">{p.cost_probability}%</span>
                          </div>
                        </td>
                        {/* Time Overrun Risk Bar + % */}
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1.5">
                            <span className="text-[11px] font-bold text-amber-600">{Math.round(p.time_overrun_months)}m</span>
                            <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-amber-500 rounded-full" style={{ width: `${Math.min(p.time_probability, 100)}%` }} />
                            </div>
                            <span className="text-[10px] text-slate-400">{p.time_probability}%</span>
                          </div>
                        </td>
                        {/* Overall Risk Score */}
                        <td className="px-4 py-3 text-center">
                          <span className="font-extrabold text-slate-900 text-xs">{p.overall_risk_pct}%</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => navigate(`/dashboard/projects/${encodeURIComponent(p.project_code)}/risk`)}
                              className="px-2.5 py-1 bg-red-600 hover:bg-red-700 text-white text-[11px] font-bold rounded-lg transition-colors inline-flex items-center gap-1 shadow-xs"
                              title="Individual Project Risk Diagnostic"
                            >
                              <ShieldAlert className="w-3 h-3" /> Risk
                            </button>
                            <button
                              onClick={() => navigate(`/dashboard/projects/${encodeURIComponent(p.project_code)}`)}
                              className="px-2 py-1 bg-white border border-slate-200 hover:border-government-blue text-government-blue hover:bg-blue-50 text-[11px] font-bold rounded-lg transition-colors"
                              title="View Project Details"
                            >
                              Details
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-3 border-t border-slate-100 bg-slate-50/40 flex items-center justify-between text-xs text-slate-500">
            <span>Showing top critical projects requiring executive intervention</span>
            <Link to="/dashboard/projects?risk=HIGH" className="font-semibold text-government-blue hover:underline flex items-center gap-1">
              View All High Risk Projects <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Right Column: Risk Heatmap Matrix (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-government-blue" />
                <h3 className="font-bold text-slate-900 text-sm">Risk Heatmap</h3>
              </div>
              <span className="text-[10px] text-slate-400 font-medium">Ministry × Risk</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-center border-collapse">
                <thead>
                  <tr className="text-[11px] text-slate-500 font-semibold border-b border-slate-200">
                    <th className="text-left py-2 px-1">Ministry</th>
                    <th className="py-2 px-1 text-red-600">High</th>
                    <th className="py-2 px-1 text-amber-600">Medium</th>
                    <th className="py-2 px-1 text-emerald-600">Low</th>
                    <th className="py-2 px-1 font-bold text-slate-700">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.heatmap.map((row) => (
                    <tr 
                      key={row.ministry} 
                      onClick={() => setSelectedMinistry(row.full_name)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="text-left py-2 px-1 font-semibold text-slate-800 max-w-[90px] truncate" title={row.full_name}>
                        {row.ministry}
                      </td>
                      <td className="py-2 px-1 font-bold bg-red-50/60 text-red-700 rounded-sm">
                        {row.high}
                      </td>
                      <td className="py-2 px-1 font-bold bg-amber-50/60 text-amber-700 rounded-sm">
                        {row.medium}
                      </td>
                      <td className="py-2 px-1 font-bold bg-emerald-50/60 text-emerald-700 rounded-sm">
                        {row.low}
                      </td>
                      <td className="py-2 px-1 font-bold text-slate-900">
                        {row.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-200 font-bold text-slate-900 bg-slate-50/80">
                    <td className="text-left py-2 px-1">Total</td>
                    <td className="py-2 px-1 text-red-700">{data.heatmap_totals.high}</td>
                    <td className="py-2 px-1 text-amber-700">{data.heatmap_totals.medium}</td>
                    <td className="py-2 px-1 text-emerald-700">{data.heatmap_totals.low}</td>
                    <td className="py-2 px-1 text-government-blue">{data.heatmap_totals.total}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-3 border-t border-slate-100 flex justify-between items-center">
            <span>Click ministry to filter dashboard</span>
            <span className="text-government-blue font-semibold">Active Matrix</span>
          </div>
        </div>

      </div>

      {/* ── 5. BOTTOM ROW (Top Risk Factors, Recent Early Warnings, Ask AI) ──── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Card 1: Top Risk Factors */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-government-blue" />
              <h3 className="font-bold text-slate-900 text-sm">Top Risk Factors</h3>
            </div>

            <div className="space-y-4">
              {data.top_risk_factors.map((factor, idx) => {
                const colors = ['bg-red-500', 'bg-amber-500', 'bg-blue-500', 'bg-teal-500'];
                const barColor = colors[idx % colors.length];

                return (
                  <div key={factor.factor} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-700">{factor.factor}</span>
                      <span className="font-bold text-slate-900">{factor.percentage}%</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${Math.min(factor.percentage, 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-4 border-t border-slate-100 flex justify-between">
            <span>M3/M4 Feature Importance</span>
            <span className="text-slate-600 font-medium">Calculated Live</span>
          </div>
        </div>

        {/* Card 2: Recent Early Warnings Table */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-500" />
                <h3 className="font-bold text-slate-900 text-sm">Recent Early Warnings</h3>
              </div>
              <span className="text-xs font-semibold text-amber-600">{data.recent_early_warnings.length} Active</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="text-[11px] text-slate-400 border-b border-slate-100 font-semibold">
                  <tr>
                    <th className="py-2">Project Name</th>
                    <th className="py-2 text-center">Risk Type</th>
                    <th className="py-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.recent_early_warnings.slice(0, 4).map((w) => (
                    <tr key={w.project_code} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 font-medium text-slate-800 max-w-[140px] truncate" title={w.project_name}>
                        <Link to={`/dashboard/projects/${encodeURIComponent(w.project_code)}`} className="hover:text-government-blue">
                          {w.project_name}
                        </Link>
                      </td>
                      <td className="py-2.5 text-center">
                        <span className="text-[11px] font-bold text-red-600">
                          {w.risk_type}
                        </span>
                      </td>
                      <td className="py-2.5 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          w.status === 'Open' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {w.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-3 border-t border-slate-100 flex justify-between items-center">
            <span>Automated M5 anomaly detection</span>
            <Link to="/dashboard/projects" className="text-government-blue font-semibold hover:underline">
              View all warnings
            </Link>
          </div>
        </div>

        {/* Card 3: Ask InfraGuard-AI */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-8 h-8 rounded-lg bg-government-blue text-white flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                  Ask InfraGuard-AI
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                </h3>
                <p className="text-[11px] text-slate-500">
                  Insights & explanations grounded in real DB & ML models.
                </p>
              </div>
            </div>

            {/* AI Response Display if available */}
            {aiResponse ? (
              <div className="my-3 p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs space-y-2">
                <div className="flex justify-between items-start">
                  <span className="font-bold text-government-blue flex items-center gap-1">
                    <Bot className="w-3.5 h-3.5" /> Intelligence Output
                  </span>
                  <button onClick={() => setAiResponse(null)} className="text-slate-400 hover:text-slate-600">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-slate-700 leading-relaxed max-h-28 overflow-y-auto">
                  {aiResponse}
                </p>
                {aiSources.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-1">
                    {aiSources.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 bg-white border border-slate-200 text-[9px] font-semibold text-slate-600 rounded">
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : null}

            {/* Input Box */}
            <form 
              onSubmit={(e) => { e.preventDefault(); handleAiAsk(); }}
              className="relative mt-3 mb-2.5"
            >
              <input
                type="text"
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                placeholder="Ask about project risk, cost overrun, delays..."
                disabled={aiLoading}
                className="w-full pl-3.5 pr-10 py-2.5 border border-slate-200 rounded-xl text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-government-blue shadow-xs"
              />
              <button
                type="submit"
                disabled={aiLoading || !aiQuestion.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 bg-government-blue text-white rounded-lg flex items-center justify-center hover:bg-blue-800 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {aiLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              </button>
            </form>

            {/* Quick Suggestion Chips */}
            <div className="flex flex-wrap gap-1.5">
              {[
                'Why is this project high risk?',
                'Which projects need attention?',
                'What are the risk factors?'
              ].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => { setAiQuestion(chip); handleAiAsk(chip); }}
                  className="px-2.5 py-1 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-lg text-[10px] font-semibold text-slate-600 hover:text-government-blue transition-colors cursor-pointer"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          <div className="text-[11px] text-slate-400 pt-3 border-t border-slate-100 flex justify-between items-center">
            <span>Powered by Groq & RAG Pipeline</span>
            <span className="text-emerald-600 font-semibold">Zero Hallucination Mode</span>
          </div>
        </div>

      </div>

    </div>
  );
};

export default RiskAssessment;
