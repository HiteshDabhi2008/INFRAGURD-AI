
import { Link } from 'react-router-dom';
import { Shield, Activity, BarChart3, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-government-blue p-2 rounded-lg">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold text-government-blue block leading-none">InfraGuard-AI</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Government of India</span>
          </div>
        </div>
        
        <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-600">
          <a href="#features" className="hover:text-government-blue transition-colors">Features</a>
          <a href="#monitoring" className="hover:text-government-blue transition-colors">Monitoring</a>
          <a href="#analytics" className="hover:text-government-blue transition-colors">Analytics</a>
          <a href="#contact" className="hover:text-government-blue transition-colors">Contact</a>
        </div>

        <div className="flex items-center space-x-4">
          <Link to="/register" className="text-sm font-medium text-slate-600 hover:text-government-blue transition-colors hidden sm:block">
            Authority Registration
          </Link>
          <Link to="/login" className="bg-government-blue hover:bg-blue-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-sm">
            <Shield className="w-4 h-4" />
            Authority Login
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1">
        <div className="relative overflow-hidden bg-government-blue text-white">
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1545464333-9cbd1f263054?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80')] bg-cover bg-center opacity-10 mix-blend-overlay"></div>
          
          <div className="max-w-7xl mx-auto px-6 py-24 lg:py-32 relative z-10">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-sm font-medium mb-6">
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
                  Next-Gen Project Intelligence
                </div>
                <h1 className="text-5xl lg:text-6xl font-bold leading-tight mb-6">
                  Intelligent Monitoring for India's Infrastructure Projects
                </h1>
                <p className="text-xl text-blue-100 mb-10 max-w-xl">
                  Transforming project monitoring into predictive, risk-aware and data-driven infrastructure management using advanced AI analytics.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/login" className="bg-teal-500 hover:bg-teal-600 text-white px-8 py-3.5 rounded-lg text-base font-medium transition-colors flex items-center justify-center gap-2 shadow-lg">
                    Authority Login
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                  <a href="#explore" className="bg-white/10 hover:bg-white/20 border border-white/20 text-white px-8 py-3.5 rounded-lg text-base font-medium transition-colors flex items-center justify-center backdrop-blur-sm">
                    Explore Platform
                  </a>
                </div>
              </div>

              {/* Abstract Visual / Dashboard Preview */}
              <div className="relative">
                <div className="absolute -inset-1 bg-gradient-to-r from-teal-400 to-blue-500 rounded-2xl blur opacity-30"></div>
                <div className="relative bg-slate-900/80 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl">
                  <div className="flex items-center gap-2 mb-6">
                    <div className="w-3 h-3 rounded-full bg-red-400"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                    <div className="w-3 h-3 rounded-full bg-green-400"></div>
                  </div>
                  
                  <div className="space-y-4">
                    {/* Decorative Chart Visual */}
                    <div className="flex justify-between items-end h-32 gap-2 border-b border-white/10 pb-4">
                      {[40, 70, 45, 90, 65, 85, 30].map((h, i) => (
                        <div key={i} className="w-full bg-government-blue rounded-t-sm relative group">
                          <div style={{ height: `${h}%` }} className="absolute bottom-0 w-full bg-teal-500 rounded-t-sm transition-all duration-1000"></div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Floating Cards */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-blue-200 text-sm mb-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400" /> Cost Risk
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-400 w-3/4"></div>
                        </div>
                      </div>
                      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-blue-200 text-sm mb-2">
                          <Clock className="w-4 h-4 text-red-400" /> Time Risk
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-red-400 w-5/6"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-black">Predictive Infrastructure Intelligence</h2>
              <p className="mt-4 text-lg text-slate-600">Beyond monitoring, we predict outcomes to enable proactive decision making.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 text-government-blue rounded-xl flex items-center justify-center mb-6">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-black mb-3">Cost & Time Prediction</h3>
                <p className="text-slate-600">Advanced Machine Learning models analyze 4-month historical trends to predict final project costs and completion delays.</p>
              </div>
              <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-teal-100 text-teal-700 rounded-xl flex items-center justify-center mb-6">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-black mb-3">Multi-factor Risk Engine</h3>
                <p className="text-slate-600">Automated risk assessment scoring projects based on expenditure gaps, physical progress, and predicted overruns.</p>
              </div>
              <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-xl flex items-center justify-center mb-6">
                  <Shield className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-black mb-3">Role-Based Intelligence</h3>
                <p className="text-slate-600">Secure, personalized dashboards for Ministry, Department, and Agency officers with strict data access controls.</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-slate-900 text-slate-400 py-12 text-sm">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-government-blue" />
              <span className="text-lg font-bold text-white">InfraGuard-AI</span>
            </div>
            <p className="max-w-md">
              A predictive project monitoring and risk intelligence platform built for the Government of India, helping authorities build better infrastructure, smarter and faster.
            </p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Platform</h4>
            <ul className="space-y-2">
              <li><Link to="/login" className="hover:text-white transition-colors">Authority Login</Link></li>
              <li><Link to="/register" className="hover:text-white transition-colors">Registration</Link></li>
              <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">User Manual</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Support Desk</a></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center">
          <p>© 2026 InfraGuard-AI. SIH 2026 Problem Statement: 26103.</p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
