import React, { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import { scaleQuantize } from 'd3-scale';
import { 
  Map as MapIcon, AlertTriangle, ShieldAlert, Clock, 
  Activity, Layers, ChevronRight, X, BarChart3
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  Tooltip, Legend, CartesianGrid 
} from 'recharts';
import { analyticsApi } from '../../services/api';
import type { StateMapAnalytics, StateStat, StateProjectItem } from '../../services/api';

const INDIA_GEO_JSON = "/india.json";

type VisMode = 'project_distribution' | 'high_risk_projects' | 'critical_projects' | 'delayed_projects' | 'average_physical_progress';

export const StateView: React.FC = () => {
  const [data, setData] = useState<StateMapAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<VisMode>('project_distribution');

  // Tooltip & Hover state
  const [hoveredState, setHoveredState] = useState<{
    name: string;
    stats?: StateStat;
    x: number;
    y: number;
  } | null>(null);

  // Selected State Drawer
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [drawerProjects, setDrawerProjects] = useState<StateProjectItem[]>([]);
  const [loadingDrawer, setLoadingDrawer] = useState(false);

  useEffect(() => {
    fetchStateData();
  }, []);

  const fetchStateData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.getStateMap();
      setData(res.data);
    } catch (err) {
      console.error('Failed to load state map data', err);
      setError('Unable to load state geospatial analytics.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectState = async (stateName: string) => {
    setSelectedState(stateName);
    setLoadingDrawer(true);
    try {
      const res = await analyticsApi.getStateProjects(stateName);
      setDrawerProjects(res.data.projects);
    } catch (err) {
      console.error('Failed to load state projects', err);
      setDrawerProjects([]);
    } finally {
      setLoadingDrawer(false);
    }
  };

  // Compute choropleth scale based on active mode
  const getColorScale = () => {
    if (!data) return () => '#f1f5f9';
    const statsList = Object.values(data.state_stats);

    switch (mode) {
      case 'high_risk_projects': {
        const maxVal = Math.max(...statsList.map((s) => s.high_risk_count), 1);
        return scaleQuantize<string>()
          .domain([0, maxVal])
          .range(['#ffedd5', '#fed7aa', '#fdba74', '#fb923c', '#f97316', '#ea580c', '#c2410c', '#9a3412']);
      }
      case 'critical_projects': {
        const maxVal = Math.max(...statsList.map((s) => s.critical_count), 1);
        return scaleQuantize<string>()
          .domain([0, maxVal])
          .range(['#fee2e2', '#fecaca', '#fca5a5', '#f87171', '#ef4444', '#dc2626', '#b91c1c', '#7f1d1d']);
      }
      case 'delayed_projects': {
        const maxVal = Math.max(...statsList.map((s) => s.delayed_count), 1);
        return scaleQuantize<string>()
          .domain([0, maxVal])
          .range(['#fef3c7', '#fde68a', '#fcd34d', '#fbbf24', '#f59e0b', '#d97706', '#b45309', '#78350f']);
      }
      case 'average_physical_progress': {
        return scaleQuantize<string>()
          .domain([0, 100])
          .range(['#ecfdf5', '#d1fae5', '#a7f3d0', '#6ee7b7', '#34d399', '#10b981', '#059669', '#047857']);
      }
      case 'project_distribution':
      default: {
        const maxVal = Math.max(...statsList.map((s) => s.project_count), 1);
        return scaleQuantize<string>()
          .domain([0, maxVal])
          .range(['#eff6ff', '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8']);
      }
    }
  };

  const getMetricValue = (stats?: StateStat): number => {
    if (!stats) return 0;
    switch (mode) {
      case 'high_risk_projects': return stats.high_risk_count;
      case 'critical_projects': return stats.critical_count;
      case 'delayed_projects': return stats.delayed_count;
      case 'average_physical_progress': return stats.avg_progress;
      case 'project_distribution':
      default: return stats.project_count;
    }
  };

  const getMetricLabel = (): string => {
    switch (mode) {
      case 'high_risk_projects': return 'High Risk Projects';
      case 'critical_projects': return 'Critical Projects';
      case 'delayed_projects': return 'Delayed Projects';
      case 'average_physical_progress': return 'Avg Physical Progress';
      case 'project_distribution':
      default: return 'Total Projects';
    }
  };

  const colorScale = getColorScale();

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 font-medium">
        <div className="w-9 h-9 border-3 border-government-blue border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Aggregating Geospatial Infrastructure Data across 36 States & UTs...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 rounded-xl border border-red-200">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-bold">{error || 'Data could not be retrieved.'}</p>
        <button onClick={fetchStateData} className="mt-3 px-4 py-1.5 bg-red-600 text-white rounded-lg text-xs font-semibold">
          Retry Loading
        </button>
      </div>
    );
  }

  const { summary } = data;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <MapIcon className="w-7 h-7 text-government-blue" />
            State-wise Infrastructure Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Interactive national geospatial mapping, state risk distribution, and project monitoring
          </p>
        </div>

        {/* Visualization Mode Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 overflow-x-auto">
          {[
            { id: 'project_distribution', label: 'Projects', icon: Layers },
            { id: 'high_risk_projects', label: 'High Risk', icon: AlertTriangle },
            { id: 'critical_projects', label: 'Critical', icon: ShieldAlert },
            { id: 'delayed_projects', label: 'Delayed', icon: Clock },
            { id: 'average_physical_progress', label: 'Avg Progress %', icon: Activity },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setMode(item.id as VisMode)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                mode === item.id
                  ? 'bg-white text-government-blue shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <item.icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Overview Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">States Covered</div>
          <div className="text-2xl font-black text-slate-900 mt-1">{summary.total_states}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">States & Union Territories</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Projects</div>
          <div className="text-2xl font-black text-slate-900 mt-1">{summary.total_projects.toLocaleString()}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Central sector projects</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Sanctioned Cost</div>
          <div className="text-2xl font-black text-slate-900 mt-1">₹{(summary.total_cost / 1000).toFixed(1)}k <span className="text-xs font-semibold text-slate-500">Cr</span></div>
          <div className="text-[10px] text-slate-400 mt-0.5">Total investment</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Expenditure</div>
          <div className="text-2xl font-black text-slate-900 mt-1">₹{(summary.total_expenditure / 1000).toFixed(1)}k <span className="text-xs font-semibold text-slate-500">Cr</span></div>
          <div className="text-[10px] text-slate-400 mt-0.5">Cumulative utilization</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-red-600 uppercase tracking-wider">High & Critical Risk</div>
          <div className="text-2xl font-black text-red-700 mt-1">{summary.high_risk_projects}</div>
          <div className="text-[10px] text-red-500 mt-0.5">{summary.critical_projects} Critical projects</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-amber-600 uppercase tracking-wider">Delayed Projects</div>
          <div className="text-2xl font-black text-amber-700 mt-1">{summary.delayed_projects}</div>
          <div className="text-[10px] text-amber-600 mt-0.5">Schedule slippage flagged</div>
        </div>
      </div>

      {/* Main Map & Top State Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Interactive Map */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs lg:col-span-2 relative">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <MapIcon className="w-4 h-4 text-government-blue" />
                India Infrastructure Choropleth — {getMetricLabel()}
              </h3>
              <p className="text-xs text-slate-500">
                Hover over any state to inspect metrics. Click to open detailed project breakdown.
              </p>
            </div>

            {/* Mode Tag */}
            <span className="self-start sm:self-auto px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold">
              Mode: <strong className="text-government-blue">{getMetricLabel()}</strong>
            </span>
          </div>

          <div className="bg-slate-50 rounded-xl border border-slate-200 h-[560px] flex items-center justify-center overflow-hidden relative">
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{
                scale: 950,
                center: [82.5, 22.5],
              }}
              className="w-full h-full"
            >
              <Geographies geography={INDIA_GEO_JSON}>
                {({ geographies }) =>
                  geographies.map((geo) => {
                    const rawName = geo?.properties?.NAME_1 || geo?.properties?.name;
                    const stats = data.state_stats[rawName];
                    const val = getMetricValue(stats);
                    const fillColor = stats && val > 0 ? colorScale(val) : '#e2e8f0';

                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        fill={fillColor}
                        stroke="#94a3b8"
                        strokeWidth={0.6}
                        onClick={() => {
                          if (rawName) handleSelectState(rawName);
                        }}
                        onMouseEnter={(e) => {
                          setHoveredState({
                            name: rawName,
                            stats,
                            x: e.clientX,
                            y: e.clientY,
                          });
                        }}
                        onMouseLeave={() => {
                          setHoveredState(null);
                        }}
                        style={{
                          default: { outline: 'none', transition: 'fill 0.2s' },
                          hover: { fill: '#3b82f6', outline: 'none', cursor: 'pointer' },
                          pressed: { fill: '#1d4ed8', outline: 'none' },
                        } as any}
                      />
                    );
                  })
                }
              </Geographies>
            </ComposableMap>

            {/* Floating Hover Tooltip */}
            {hoveredState && (
              <div className="absolute top-4 right-4 bg-slate-900/95 text-white p-4 rounded-xl shadow-xl border border-slate-700 pointer-events-none text-xs w-64 backdrop-blur-xs space-y-2 animate-in fade-in duration-100">
                <div className="flex items-center justify-between border-b border-slate-700 pb-2">
                  <span className="font-bold text-sm text-white">{hoveredState.name}</span>
                  <span className="text-[10px] text-blue-300 uppercase font-mono">Click for list</span>
                </div>

                {hoveredState.stats ? (
                  <div className="space-y-1.5 pt-0.5">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Total Projects:</span>
                      <strong className="text-white">{hoveredState.stats.project_count}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">High / Critical:</span>
                      <strong className="text-red-400">
                        {hoveredState.stats.high_risk_count + hoveredState.stats.critical_count}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Delayed Projects:</span>
                      <strong className="text-amber-400">{hoveredState.stats.delayed_count}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Avg Progress:</span>
                      <strong className="text-emerald-400">{hoveredState.stats.avg_progress}%</strong>
                    </div>
                    <div className="flex justify-between border-t border-slate-800 pt-1.5">
                      <span className="text-slate-400">Investment:</span>
                      <strong className="text-white">₹{Math.round(hoveredState.stats.revised_cost).toLocaleString()} Cr</strong>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-400 py-1">No major central projects registered.</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: High Attention States & Quick Actions */}
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              High Attention States
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              States with the highest concentration of projects requiring active IPMD intervention.
            </p>

            <div className="space-y-3">
              {Object.values(data.state_stats)
                .filter((s) => s.high_risk_count > 0 || s.critical_count > 0)
                .sort((a, b) => (b.critical_count * 2 + b.high_risk_count) - (a.critical_count * 2 + a.high_risk_count))
                .slice(0, 5)
                .map((st) => (
                  <button
                    key={st.state_name}
                    onClick={() => handleSelectState(st.state_name)}
                    className="w-full text-left p-3 rounded-xl border border-slate-100 bg-slate-50 hover:bg-blue-50/60 hover:border-blue-200 transition-all flex items-center justify-between group"
                  >
                    <div>
                      <div className="font-bold text-sm text-slate-900 group-hover:text-blue-700">
                        {st.state_name}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {st.project_count} projects • ₹{Math.round(st.revised_cost).toLocaleString()} Cr
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        st.critical_count > 0 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {st.critical_count > 0 ? `${st.critical_count} CRITICAL` : `${st.high_risk_count} HIGH`}
                      </span>
                      <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-end gap-1">
                        <span>Details</span>
                        <ChevronRight className="w-3 h-3" />
                      </div>
                    </div>
                  </button>
                ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-government-blue to-blue-900 text-white p-5 rounded-2xl shadow-xs space-y-3">
            <h4 className="text-sm font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-200" />
              State Schedule Delay Overview
            </h4>
            <p className="text-xs text-blue-100 leading-relaxed">
              States with the highest average project delay months. Track delay factors to prevent cost escalations.
            </p>
            <div className="space-y-2 pt-1 text-xs">
              {data.delay_analysis_by_state.slice(0, 3).map((s) => (
                <div key={s.state} className="flex justify-between items-center py-1 border-b border-white/10 last:border-0">
                  <span className="font-medium text-white">{s.state}</span>
                  <span className="font-mono text-amber-300 font-bold">{s.avg_delay_months} mo avg</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 5 Analytical Charts Section */}
      <div className="space-y-6 pt-4">
        <div className="border-b border-slate-200 pb-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-government-blue" />
            Comprehensive State Analytics & Trends
          </h2>
          <p className="text-xs text-slate-500">
            Cross-state comparative analysis covering risk distributions, delays, physical execution, and capital allocation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart 1: Delay Analysis */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Chart 1: Delay Analysis by State</h3>
              <span className="text-[11px] text-slate-400">Delayed projects count</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.delay_analysis_by_state} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="state" angle={-30} textAnchor="end" interval={0} tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="delayed_projects" fill="#f59e0b" name="Delayed Projects" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Risk Distribution by State (Stacked Bar) */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Chart 2: Risk Category Distribution by State</h3>
              <span className="text-[11px] text-slate-400">Stacked risk levels</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.risk_distribution_by_state} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="state" angle={-30} textAnchor="end" interval={0} tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="LOW" stackId="a" fill="#10b981" name="Low Risk" />
                  <Bar dataKey="MEDIUM" stackId="a" fill="#f59e0b" name="Medium Risk" />
                  <Bar dataKey="HIGH" stackId="a" fill="#f97316" name="High Risk" />
                  <Bar dataKey="CRITICAL" stackId="a" fill="#ef4444" name="Critical Risk" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Top States by Projects */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Chart 3: Top States by Project Volume</h3>
              <span className="text-[11px] text-slate-400">Active projects count</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.top_states_by_projects} layout="vertical" margin={{ top: 10, right: 20, left: 30, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="state" type="category" tick={{ fontSize: 10 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="projects" fill="#1e40af" name="Total Projects" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 4: Average Physical Progress */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Chart 4: Average Physical Execution Progress (%)</h3>
              <span className="text-[11px] text-slate-400">Execution completion rate</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.avg_progress_by_state} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="state" angle={-30} textAnchor="end" interval={0} tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="avg_progress" fill="#059669" name="Avg Progress %" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Chart 5: State Financial Overview (Full Width) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Chart 5: State Capital Allocation vs Cumulative Expenditure (₹ Cr)</h3>
              <p className="text-xs text-slate-500">Comparing sanctioned project costs with actual capital expenditure</p>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">Top 10 States by Investment</span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.financial_overview_by_state} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="state" angle={-25} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="revised_cost" fill="#3b82f6" name="Sanctioned / Revised Cost (₹ Cr)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="cumulative_expenditure" fill="#10b981" name="Cumulative Expenditure (₹ Cr)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* State Projects Drawer */}
      {selectedState && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white w-full max-w-4xl h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="bg-government-blue text-white px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <MapIcon className="w-5 h-5 text-blue-200" />
                  {selectedState} — Infrastructure Portfolio
                </h3>
                <p className="text-xs text-blue-200">
                  {drawerProjects.length} Central Sector Projects monitored in {selectedState}
                </p>
              </div>
              <button
                onClick={() => setSelectedState(null)}
                className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingDrawer ? (
                <div className="py-16 text-center text-slate-400">Loading projects for {selectedState}...</div>
              ) : drawerProjects.length === 0 ? (
                <div className="py-16 text-center text-slate-400">No project records found for {selectedState}.</div>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                      <tr>
                        <th className="py-3 px-4">Project</th>
                        <th className="py-3 px-3">Agency / Sector</th>
                        <th className="py-3 px-3">Cost (₹ Cr)</th>
                        <th className="py-3 px-3">Progress</th>
                        <th className="py-3 px-3">Delay</th>
                        <th className="py-3 px-3">Risk</th>
                        <th className="py-3 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {drawerProjects.map((p) => (
                        <tr key={p.project_code} className="hover:bg-blue-50/40 transition-colors">
                          <td className="py-3 px-4">
                            <div className="font-mono font-bold text-government-blue">{p.project_code}</div>
                            <div className="text-slate-800 line-clamp-1 font-medium">{p.project_name}</div>
                          </td>
                          <td className="py-3 px-3 text-slate-600">
                            <div>{p.agency || 'Agency'}</div>
                            <div className="text-[10px] text-slate-400">{p.sector || 'Sector'}</div>
                          </td>
                          <td className="py-3 px-3 font-semibold text-slate-900">
                            ₹{p.revised_cost?.toLocaleString() || p.original_cost?.toLocaleString() || 0}
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-bold text-slate-800">{p.physical_progress ?? 0}%</div>
                            <div className="w-16 bg-slate-200 h-1 rounded-full mt-1 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-full"
                                style={{ width: `${Math.min(p.physical_progress || 0, 100)}%` }}
                              />
                            </div>
                          </td>
                          <td className="py-3 px-3">
                            {p.time_overrun_months && p.time_overrun_months > 0 ? (
                              <span className="text-amber-700 font-bold">+{p.time_overrun_months} mo</span>
                            ) : (
                              <span className="text-slate-400 font-medium">On Track</span>
                            )}
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              p.overall_risk === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                              p.overall_risk === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                              p.overall_risk === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                              'bg-emerald-100 text-emerald-700'
                            }`}>
                              {p.overall_risk || 'LOW'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <Link
                                to={`/dashboard/projects/${encodeURIComponent(p.project_code)}`}
                                className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-semibold transition-colors"
                              >
                                View
                              </Link>
                              <Link
                                to={`/dashboard/projects/${encodeURIComponent(p.project_code)}/risk`}
                                className="px-2 py-1 bg-red-50 hover:bg-red-100 text-red-700 rounded text-[11px] font-semibold transition-colors flex items-center gap-1"
                              >
                                <ShieldAlert className="w-3 h-3 text-red-600" />
                                Risk
                              </Link>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StateView;
