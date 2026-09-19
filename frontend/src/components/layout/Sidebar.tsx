
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Building2, 
  PieChart, 
  Map, 
  FolderKanban, 
  PlusCircle, 
  AlertTriangle, 
  Activity, 
  FileText, 
  Bot,
  Users,
  UserCircle
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = () => {
  const { user } = useAuth();
  
  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Ministry-wise', path: '/dashboard/ministry', icon: Building2 },
    { name: 'Sector-wise', path: '/dashboard/sector', icon: PieChart },
    { name: 'State-wise', path: '/dashboard/state', icon: Map },
    { name: 'Projects', path: '/dashboard/projects', icon: FolderKanban },
    { name: 'Newly Added', path: '/dashboard/new-projects', icon: PlusCircle },
    { name: 'Risk Intelligence', path: '/dashboard/risk', icon: AlertTriangle },
    { name: 'Reports', path: '/dashboard/reports', icon: FileText },
    { name: 'AI Assistant', path: '/dashboard/ai', icon: Bot },
    { name: 'User Profile', path: '/dashboard/profile', icon: UserCircle },
  ];

  const adminItems = [
    { name: 'Users & Roles', path: '/dashboard/profile', icon: Users },
  ];

  const isAdmin = user?.role === 'Super Admin' || user?.authority_type === 'Super Admin';

  return (
    <aside className="w-64 bg-government-blue text-white flex flex-col h-screen fixed top-0 left-0">
      <div className="p-6 border-b border-blue-800/50 flex items-center gap-3">
        <div className="bg-white p-1.5 rounded-lg">
          <Activity className="w-6 h-6 text-government-blue" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight tracking-wide">InfraGuard-AI</h1>
          <p className="text-[10px] text-blue-200 tracking-wider uppercase">Project Monitoring</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-4 custom-scrollbar">
        <nav className="px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium ${
                  isActive
                    ? 'bg-blue-800 text-white shadow-sm'
                    : 'text-blue-100 hover:bg-blue-800/50 hover:text-white'
                }`
              }
              end={item.path === '/dashboard'}
            >
              <item.icon className="w-5 h-5 opacity-90" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        {isAdmin && (
          <div className="mt-8">
            <h3 className="px-6 text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2">
              Administration
            </h3>
            <nav className="px-3 space-y-1">
              {adminItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium ${
                      isActive
                        ? 'bg-blue-800 text-white shadow-sm'
                        : 'text-blue-100 hover:bg-blue-800/50 hover:text-white'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5 opacity-90" />
                  {item.name}
                </NavLink>
              ))}
            </nav>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-blue-800/50 text-xs text-blue-300 flex justify-between items-center">
        <span>System: Online</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>Live</span>
      </div>
    </aside>
  );
};

export default Sidebar;
