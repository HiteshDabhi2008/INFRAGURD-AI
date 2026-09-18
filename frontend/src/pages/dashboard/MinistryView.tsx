import { Building2, TrendingUp, ArrowRight } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { Link } from 'react-router-dom';

const ministryData = [
  { name: 'MoRTH', projects: 125, expenditure: 45000, risk: 'High', color: '#1e3a8a' }, // Road Transport
  { name: 'MoHUA', projects: 85, expenditure: 28000, risk: 'Medium', color: '#0ea5e9' }, // Housing & Urban
  { name: 'MoR', projects: 64, expenditure: 32000, risk: 'Medium', color: '#0f766e' }, // Railways
  { name: 'MoP', projects: 42, expenditure: 18000, risk: 'Low', color: '#6366f1' }, // Power
  { name: 'MNRE', projects: 38, expenditure: 12000, risk: 'Low', color: '#10b981' }, // Renewable Energy
];


const MinistryView = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Ministry-wise Analysis</h1>
          <p className="text-sm text-slate-500">Performance and risk overview across central ministries</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Expenditure Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-government-blue" /> Expenditure by Ministry
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ministryData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{fontSize: 12, fill: '#64748b'}} axisLine={false} tickLine={false} />
                <YAxis tick={{fontSize: 12, fill: '#64748b'}} axisLine={false} tickLine={false} tickFormatter={(val) => `₹${val/1000}k`} />
                <RechartsTooltip 
                  formatter={(value: any) => [`₹${value} Cr`, 'Expenditure']}
                  cursor={{fill: '#f1f5f9'}}
                />
                <Bar dataKey="expenditure" radius={[4, 4, 0, 0]}>
                  {ministryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Project Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-government-blue" /> Project Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={ministryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="projects"
                >
                  {ministryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip formatter={(value: any) => [value, 'Projects']} />
                <Legend layout="vertical" verticalAlign="middle" align="right" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Ministry Details Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h3 className="text-lg font-bold text-black">Ministry Portfolio Detail</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-semibold text-slate-700">Ministry</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Active Projects</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-right">Total Exp (₹ Cr)</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Avg Progress</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Portfolio Risk</th>
                <th className="px-6 py-4 font-semibold text-slate-700"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {ministryData.map((ministry) => (
                <tr key={ministry.name} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-black flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{backgroundColor: ministry.color}}></div>
                    {ministry.name}
                  </td>
                  <td className="px-6 py-4 text-center font-medium text-slate-700">{ministry.projects}</td>
                  <td className="px-6 py-4 text-right font-medium text-slate-700">{ministry.expenditure.toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-slate-700 font-medium">45%</span>
                      <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-government-blue w-[45%]"></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                      ministry.risk === 'High' ? 'bg-red-100 text-red-800' :
                      ministry.risk === 'Medium' ? 'bg-amber-100 text-amber-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {ministry.risk}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link to={`/dashboard/projects?ministry=${ministry.name}`} className="text-government-blue hover:text-blue-800 text-xs font-semibold inline-flex items-center">
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
