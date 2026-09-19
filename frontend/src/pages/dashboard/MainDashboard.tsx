import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Building2, CheckCircle, FolderKanban, IndianRupee, Map, PieChart, TrendingUp, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../services/api';

interface Overview {
  total_projects: number;
  ongoing_projects: number;
  high_risk_projects: number;
  critical_risk_projects: number;
  original_cost_total: number;
  total_expenditure: number;
  average_physical_progress: number;
  risk_distribution: Array<{ name: string; value: number }>;
}

const formatCrore = (value: number) => `₹${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} Cr`;

const MainDashboard = () => {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { analyticsApi.overview().then(({ data }) => setOverview(data)).catch(() => setError('Unable to load dashboard data.')); }, []);

  if (error) return <p className="p-8 text-center text-red-600">{error}</p>;
  if (!overview) return <p className="p-8 text-center text-slate-500">Loading dashboard data...</p>;

  const cards = [
    { label: 'Total Projects', value: overview.total_projects, icon: FolderKanban, link: '/dashboard/projects' },
    { label: 'Ongoing Projects', value: overview.ongoing_projects, icon: Activity, link: '/dashboard/projects' },
    { label: 'High Risk Projects', value: overview.high_risk_projects, icon: AlertTriangle, link: '/dashboard/projects?risk=HIGH' },
    { label: 'Critical Projects', value: overview.critical_risk_projects, icon: AlertTriangle, link: '/dashboard/projects?risk=CRITICAL' },
    { label: 'Approved Cost', value: formatCrore(overview.original_cost_total), icon: IndianRupee, link: '/dashboard/projects' },
    { label: 'Expenditure', value: formatCrore(overview.total_expenditure), icon: TrendingUp, link: '/dashboard/projects' },
  ];
  const modules = [
    ['Ministry-wise', Building2, '/dashboard/ministry'], ['Sector-wise', PieChart, '/dashboard/sector'], ['State-wise', Map, '/dashboard/state'], ['Projects', FolderKanban, '/dashboard/projects']
  ] as const;

  return <div className="space-y-6">
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 className="text-2xl font-bold text-black">Infrastructure Intelligence Dashboard</h1>
        <p className="text-sm text-slate-500">Live portfolio metrics from authorized project records.</p>
      </div>
      <div className="flex items-center gap-2">
        <Link 
          to="/dashboard/reports" 
          className="flex items-center gap-2 px-3.5 py-2 text-slate-700 bg-white border border-slate-200 rounded-lg text-sm font-semibold hover:bg-slate-50 transition-colors shadow-xs"
        >
          <FileText className="w-4 h-4 text-government-blue" />
          <span>Executive Reports</span>
        </Link>
        <Link 
          to="/dashboard/projects" 
          className="flex items-center gap-2 px-4 py-2 bg-government-blue text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors shadow-sm"
        >
          <FolderKanban className="w-4 h-4" />
          <span>Explore Projects</span>
        </Link>
      </div>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">{cards.map(({ label, value, icon: Icon, link }) => <Link key={label} to={link} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-government-blue"><Icon className="w-5 h-5 text-government-blue mb-4" /><div className="text-2xl font-bold text-black">{value}</div><div className="text-xs text-slate-500 font-medium">{label}</div></Link>)}</div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><h2 className="font-bold mb-4">Portfolio Views</h2><div className="grid grid-cols-2 gap-3">{modules.map(([label, Icon, path]) => <Link key={label} to={path} className="p-4 border border-slate-200 rounded-lg text-center hover:border-government-blue"><Icon className="mx-auto mb-2 w-6 h-6 text-government-blue" /><span className="text-sm font-semibold">{label}</span></Link>)}</div></section>
      <section className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><h2 className="font-bold mb-4">Risk Distribution</h2>{overview.risk_distribution.length === 0 ? <p className="text-slate-500">No risk assessments available.</p> : <div className="space-y-4">{overview.risk_distribution.map((item) => <Link key={item.name} to={`/dashboard/projects?risk=${encodeURIComponent(item.name === 'UNASSESSED' ? '' : item.name)}`} className="flex items-center gap-3"><span className="w-28 text-sm text-slate-600">{item.name}</span><div className="flex-1 h-3 bg-slate-100 rounded-full"><div className="h-full bg-government-blue rounded-full" style={{ width: `${overview.total_projects ? (item.value / overview.total_projects) * 100 : 0}%` }} /></div><span className="w-8 text-right font-semibold">{item.value}</span></Link>)}</div>}</section>
    </div>
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"><div className="flex justify-between"><h2 className="font-bold flex items-center gap-2"><CheckCircle className="w-5 h-5 text-government-blue" /> Average Physical Progress</h2><span className="text-2xl font-bold">{overview.average_physical_progress}%</span></div><div className="mt-4 h-3 bg-slate-100 rounded-full"><div className="h-full bg-government-teal rounded-full" style={{ width: `${Math.min(overview.average_physical_progress, 100)}%` }} /></div></div>
  </div>;
};

export default MainDashboard;
