import { useState, useEffect } from 'react';
import { Building2, TrendingUp, ArrowRight, AlertTriangle } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../services/api';

const COLORS = ['#1e3a8a', '#0ea5e9', '#0f766e', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

interface MinistryItem {
  name: string;
  project_count: number;
  original_cost: number;
  revised_cost: number;
  expenditure: number;
  average_progress: number;
  high_risk_count: number;
  critical_count: number;
}

const MinistryView = () => {
  const [data, setData] = useState<MinistryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.ministry()
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
    return <div className="p-8 text-center text-slate-500 font-medium">Loading ministry analysis...</div>;
  }

  const topMinistries = data.slice(0, 4);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Ministry-wise Projects</h1>
          <p className="text-sm text-slate-500">Live oversight and risk distribution across Union Ministries</p>
        </div>
      </div>

      {/* Top 4 Ministry Highlight Cards (Matching reference layout) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {topMinistries.map((m) => {
          const riskLevel = m.critical_count > 0 ? 'Critical' : m.high_risk_count > 0 ? 'High' : 'Medium';
          const riskColor = riskLevel === 'Critical' ? 'bg-red-100 text-red-800' : riskLevel === 'High' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800';
          return (
            <div key={m.name} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-government-blue transition-colors">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <h3 className="font-bold text-slate-900 text-sm line-clamp-1">{m.name}</h3>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${riskColor}`}>
                    {riskLevel} Risk
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Projects:</span>
                    <span className="font-bold text-slate-900">{m.project_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Approved Cost:</span>
                    <span className="font-bold text-slate-900">₹{Math.round(m.original_cost).toLocaleString()} Cr</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Expenditure:</span>
                    <span className="font-bold text-slate-900">₹{Math.round(m.expenditure).toLocaleString()} Cr</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Progress:</span>
                    <span className="font-bold text-government-teal">{m.average_progress}%</span>
                  </div>
                </div>
              </div>
              <Link to={`/dashboard/projects?ministry=${encodeURIComponent(m.name)}`} className="mt-4 text-xs font-semibold text-government-blue hover:underline flex items-center gap-1">
                View All Projects <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expenditure Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-government-blue" /> Expenditure by Ministry (₹ Cr)
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.slice(0, 8)} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
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
                  {data.slice(0, 8).map((_, index) => (
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
            <Building2 className="w-5 h-5 text-government-blue" /> Project Count
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.slice(0, 6)}
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="project_count"
                >
                  {data.slice(0, 6).map((_, index) => (
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

      {/* Ministry Details Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center">
          <h3 className="text-lg font-bold text-black">Ministry Portfolio Detail</h3>
          <span className="text-xs text-slate-500">{data.length} Ministries Monitored</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-semibold text-slate-700">Ministry</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Active Projects</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-right">Approved Cost (₹ Cr)</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-right">Total Exp (₹ Cr)</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Avg Progress</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">High / Critical</th>
                <th className="px-6 py-4 font-semibold text-slate-700"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((ministry, idx) => (
                <tr key={ministry.name} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-black flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></div>
                    {ministry.name}
                  </td>
                  <td className="px-6 py-4 text-center font-medium text-slate-700">{ministry.project_count}</td>
                  <td className="px-6 py-4 text-right font-medium text-slate-700">₹{Math.round(ministry.original_cost).toLocaleString()}</td>
                  <td className="px-6 py-4 text-right font-medium text-slate-700">₹{Math.round(ministry.expenditure).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-slate-700 font-medium">{ministry.average_progress}%</span>
                      <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-government-teal" style={{ width: `${Math.min(ministry.average_progress, 100)}%` }}></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    {ministry.critical_count > 0 || ministry.high_risk_count > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">
                        <AlertTriangle className="w-3 h-3" />
                        {ministry.critical_count + ministry.high_risk_count}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-800">
                        0
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link to={`/dashboard/projects?ministry=${encodeURIComponent(ministry.name)}`} className="text-government-blue hover:underline text-xs font-semibold inline-flex items-center">
                      View Projects <ArrowRight className="w-3 h-3 ml-1" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MinistryView;
