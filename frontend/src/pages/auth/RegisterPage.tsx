import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '../../services/api';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    organization: '',
    department: '',
    authority_type: 'Viewer / Auditor',
    state_region: '',
    agency: '',
    designation: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      const payload = { ...formData };
      // @ts-ignore - remove confirm_password
      delete payload.confirm_password;
      
      await api.post('/api/auth/register', payload);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-sm text-center">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-black mb-2">Registration Submitted</h2>
          <p className="text-slate-600 mb-8">
            Your registration has been submitted for authority verification. You will receive an email once your account is approved and appropriate role-based access is granted.
          </p>
          <Link
            to="/login"
            className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-government-blue hover:bg-blue-800 transition-colors"
          >
            Return to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <div className="bg-government-blue p-3 rounded-xl inline-flex mb-4">
          <Activity className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-extrabold text-black">Officer Registration</h2>
        <p className="mt-2 text-sm text-slate-600">
          Request access to InfraGuard-AI
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-2xl">
        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-xl sm:px-10 border border-slate-200">
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {/* Personal Information */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Full Name</label>
                <div className="mt-1">
                  <input
                    name="full_name"
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Official Email ID</label>
                <div className="mt-1">
                  <input
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              {/* Organization Details */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Ministry / Organization</label>
                <div className="mt-1">
                  <input
                    name="organization"
                    type="text"
                    required
                    value={formData.organization}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Department</label>
                <div className="mt-1">
                  <input
                    name="department"
                    type="text"
                    value={formData.department}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Authority Role</label>
                <div className="mt-1">
                  <select
                    name="authority_type"
                    value={formData.authority_type}
                    onChange={handleChange}
                    className="block w-full pl-3 pr-10 py-2 text-base border-slate-300 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm rounded-md"
                  >
                    <option value="Viewer / Auditor">Viewer / Auditor</option>
                    <option value="Agency / Project Authority">Agency / Project Authority</option>
                    <option value="Department Authority">Department Authority</option>
                    <option value="Ministry Authority">Ministry Authority</option>
                  </select>
                </div>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Designation</label>
                <div className="mt-1">
                  <input
                    name="designation"
                    type="text"
                    value={formData.designation}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Password</label>
                <div className="mt-1">
                  <input
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
                <div className="mt-1">
                  <input
                    name="confirm_password"
                    type="password"
                    required
                    value={formData.confirm_password}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 focus:outline-none focus:ring-government-blue focus:border-government-blue sm:text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg flex gap-3 text-sm text-slate-600 mt-6 border border-slate-200">
              <ShieldCheck className="w-5 h-5 text-government-blue flex-shrink-0" />
              <p>
                By submitting this registration, you acknowledge that access to this platform is restricted to authorized personnel only. Data accessed must be treated according to government confidentiality guidelines.
              </p>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-government-blue hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-government-blue disabled:opacity-70 transition-colors"
              >
                {loading ? 'Submitting...' : 'Submit Registration'}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center text-sm text-slate-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-government-blue hover:text-blue-800">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
