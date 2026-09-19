
import { Search, User as UserIcon, LogOut, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { projectApi } from '../../services/api';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Array<{ project_code: string; project_name: string }>>([]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const search = async (value: string) => {
    setQuery(value);
    if (value.trim().length < 2) {
      setResults([]);
      return;
    }
    try {
      const response = await projectApi.search(value.trim());
      setResults(response.data);
    } catch {
      setResults([]);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-20 w-full shadow-sm">
      <div className="flex-1 flex items-center">
        <div className="relative w-96">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </span>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-md leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-1 focus:ring-government-blue focus:border-government-blue sm:text-sm transition-colors"
            placeholder="Search project by name, ID, code or agency..."
            value={query}
            onChange={(event) => search(event.target.value)}
          />
          {results.length > 0 && (
            <div className="absolute top-11 left-0 right-0 bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden z-30 max-h-80 overflow-y-auto">
              {results.map((result) => (
                <button
                  key={result.project_code}
                  onClick={() => {
                    setResults([]);
                    navigate(`/dashboard/projects/${encodeURIComponent(result.project_code)}`);
                  }}
                  className="block w-full text-left px-4 py-3 hover:bg-slate-50 border-b border-slate-100 last:border-0 transition-colors"
                >
                  <div className="text-sm font-semibold text-government-blue">{result.project_code}</div>
                  <div className="text-xs text-slate-600 truncate">{result.project_name}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-xs font-semibold text-blue-800">
          <ShieldCheck className="h-3.5 w-3.5 text-blue-700" />
          <span>MoSPI / IPMD National Infrastructure Portal</span>
        </div>

        <button
          onClick={() => navigate('/dashboard/profile')}
          className="flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-lg hover:bg-slate-100 transition-colors group cursor-pointer text-left border border-transparent hover:border-slate-200"
          title="View & Manage Profile"
        >
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-slate-900 group-hover:text-blue-700 transition-colors leading-tight">
              {user?.full_name || 'Government Officer'}
            </p>
            <p className="text-xs text-slate-500 font-mono">
              {user?.authority_type || 'Officer'}
            </p>
          </div>
          <div className="h-9 w-9 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-sm shadow-xs border border-blue-200 group-hover:scale-105 transition-transform">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="h-5 w-5" />}
          </div>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        <button 
          onClick={handleLogout}
          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          title="Sign Out"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
};

export default Header;
