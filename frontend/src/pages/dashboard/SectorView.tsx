import { Briefcase, Activity } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  Treemap
} from 'recharts';

const sectorData = [
  { name: 'Roads & Highways', size: 45000, projects: 110, risk: 65, color: '#1e3a8a' },
  { name: 'Railways', size: 32000, projects: 64, risk: 45, color: '#0f766e' },
  { name: 'Urban Transport', size: 28000, projects: 42, risk: 55, color: '#0ea5e9' },
  { name: 'Power', size: 18000, projects: 35, risk: 30, color: '#6366f1' },
  { name: 'Renewable Energy', size: 12000, projects: 28, risk: 25, color: '#10b981' },
  { name: 'Water Resources', size: 8500, projects: 45, risk: 40, color: '#3b82f6' },
  { name: 'Aviation', size: 6200, projects: 12, risk: 35, color: '#8b5cf6' },
  { name: 'Ports', size: 5400, projects: 8, risk: 50, color: '#ec4899' },
];

const SectorView = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Sector-wise Analysis</h1>
          <p className="text-sm text-slate-500">Distribution of investments and risks across infrastructure sectors</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Treemap for Investment Allocation */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold text-black mb-2 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-government-blue" /> Investment Allocation by Sector
          </h3>
          <p className="text-sm text-slate-500 mb-6">Box size represents total expenditure (₹ Cr)</p>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={sectorData}
                dataKey="size"
                aspectRatio={4 / 3}
                stroke="#fff"
                fill="#8884d8"
              >
                <RechartsTooltip 
                  formatter={(value: any, _name: any, props: any) => {
                    const item = props.payload;
                    return [`₹${value} Cr (${item.projects} projects)`, item.name];
                  }}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
              </Treemap>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Profile */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold text-black mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-amber-500" /> Sector Risk Profile
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="name" 
                  tick={{fontSize: 11, fill: '#64748b'}} 
                  axisLine={false} 
                  tickLine={false}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  tick={{fontSize: 12, fill: '#64748b'}} 
                  axisLine={false} 
                  tickLine={false} 
                  label={{ value: 'Avg Risk Score (0-100)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 12 } }}
                />
                <RechartsTooltip 
                  formatter={(value: any) => [value, 'Risk Score']}
                  cursor={{fill: '#f1f5f9'}}
                />
                <Bar dataKey="risk" fill="#f59e0b" radius={[4, 4, 0, 0]} maxBarSize={50} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
};

export default SectorView;
