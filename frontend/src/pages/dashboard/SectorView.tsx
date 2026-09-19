import { useState, useEffect } from 'react';
import { Briefcase, Activity, ArrowRight } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../services/api';

const COLORS = ['#1e3a8a', '#0ea5e9', '#0f766e', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

interface SectorItem {
  name: string;
  project_count: number;
  original_cost: number;
  revised_cost: number;
  expenditure: number;
  average_progress: number;
  high_risk_count: number;
  critical_count: number;
}

const SectorView = () => {
  const [data, setData] = useState<SectorItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.sector()
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading sector analysis...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Sector-wise Projects</h1>
          <p className="text-sm text-slate-500">Distribution of national investments, progress, and risk by infrastructure sector</p>
        </div>
      </div>

      {/* Sector Cards (Matching reference screenshot 5: Transport, Railways, Energy, Roads, etc.) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((sec, idx) => {
          const riskLevel = sec.critical_count > 0 ? 'Critical' : sec.high_risk_count > 0 ? 'High' : sec.average_progress < 40 ? 'Medium' : 'Low';
          const riskColor = riskLevel === 'Critical' ? 'bg-red-100 text-red-800' : riskLevel === 'High' ? 'bg-amber-100 text-amber-800' : riskLevel === 'Medium' ? 'bg-amber-50 text-amber-700' : 'bg-green-100 text-green-800';

          return (
            <div key={sec.name} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-government-blue transition-colors">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white" style={{ backgroundColor: COLORS[idx % COLORS.length] }}>
                      <Briefcase className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-slate-900 text-sm">{sec.name}</h3>
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${riskColor}`}>
                    {riskLevel} Risk
                  </span>
                </div>

                <div className="space-y-2 mt-4 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Projects:</span>
                    <span className="font-bold text-slate-900">{sec.project_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Approved Cost:</span>
                    <span className="font-bold text-slate-900">₹{Math.round(sec.original_cost).toLocaleString()} Cr</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Expenditure:</span>
                    <span className="font-bold text-slate-900">₹{Math.round(sec.expenditure).toLocaleString()} Cr</span>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span>Avg Progress:</span>
                      <span className="font-bold text-government-teal">{sec.average_progress}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-government-teal rounded-full" style={{ width: `${Math.min(sec.average_progress, 100)}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <Link to={`/dashboard/projects?sector=${encodeURIComponent(sec.name)}`} className="mt-4 pt-3 border-t border-slate-100 text-xs font-semibold text-government-blue hover:underline flex items-center justify-between">
                <span>Explore {sec.project_count} Projects</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expenditure Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-government-blue" /> Expenditure by Sector (₹ Cr)
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10, fill: '#64748b' }} 
                  axisLine={false} 
                  tickLine={false} 
                  angle={-30}
                  textAnchor="end"
                />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `₹${Math.round(val/1000)}k`} />
                <RechartsTooltip 
                  formatter={(value: any) => [`₹${Math.round(value).toLocaleString()} Cr`, 'Expenditure']}
                  cursor={{ fill: '#f1f5f9' }}
                />
                <Bar dataKey="expenditure" radius={[4, 4, 0, 0]}>
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Project Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-government-blue" /> Sector Project Count
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="project_count"
                >
                  {data.map((_, index) => (
                    <Cell key={`pie-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip formatter={(value: any) => [value, 'Projects']} />
                <Legend layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SectorView;
