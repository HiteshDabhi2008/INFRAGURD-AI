
import { Bell, Search, User as UserIcon, LogOut } from 'lucide-react';
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
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-10 w-full">
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
          {results.length > 0 && <div className="absolute top-11 left-0 right-0 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden z-20">{results.map((result) => <button key={result.project_code} onClick={() => { setResults([]); navigate(`/dashboard/projects/${encodeURIComponent(result.project_code)}`); }} className="block w-full text-left px-4 py-3 hover:bg-slate-50"><div className="text-sm font-semibold text-government-blue">{result.project_code}</div><div className="text-xs text-slate-600 truncate">{result.project_name}</div></button>)}</div>}
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-sm font-medium text-slate-500 hidden md:block">
          {user?.organization || 'Ministry of Road Transport & Highways'}
        </div>
        
        <button className="relative p-1 text-slate-400 hover:text-slate-500 focus:outline-none">
          <Bell className="h-6 w-6" />
          <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-government-red ring-2 ring-white"></span>
        </button>

        <div className="flex items-center gap-3 border-l border-slate-200 pl-6">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-black">{user?.full_name || 'Dr. A. Sharma'}</p>
            <p className="text-xs text-slate-500">{user?.authority_type || 'Officer'}</p>
          </div>
          <div className="h-9 w-9 rounded-full bg-slate-200 flex items-center justify-center text-slate-600">
            <UserIcon className="h-5 w-5" />
          </div>
          <button 
            onClick={handleLogout}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            title="Logout"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
