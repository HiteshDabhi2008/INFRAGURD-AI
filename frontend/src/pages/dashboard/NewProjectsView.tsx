
import { PlusCircle, CheckCircle, XCircle, Clock, FileText, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const newProjects = [
  { id: 'NP-0081', name: 'Smart Grid Expansion Phase II', ministry: 'MoP', submittedBy: 'State EB (Karnataka)', date: '12 Sep 2026', cost: 1250, status: 'Pending Review' },
  { id: 'NP-0082', name: 'Pune Metro Line 4', ministry: 'MoHUA', submittedBy: 'Maha Metro', date: '10 Sep 2026', cost: 4500, status: 'Under Evaluation' },
  { id: 'NP-0083', name: 'Coastal Highway (Mumbai-Goa)', ministry: 'MoRTH', submittedBy: 'NHAI', date: '08 Sep 2026', cost: 18000, status: 'Approved' },
  { id: 'NP-0084', name: 'Solar Park 500MW', ministry: 'MNRE', submittedBy: 'SECI', date: '05 Sep 2026', cost: 2100, status: 'Returned for Clarification' },
];

const NewProjectsView = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">Newly Added Projects</h1>
          <p className="text-sm text-slate-500">Review and manage recently submitted infrastructure projects</p>
        </div>
        <div className="flex gap-2">
          <Link to="/dashboard/new-projects/add" className="flex items-center gap-2 px-4 py-2 bg-government-blue text-white rounded-lg text-sm font-medium hover:bg-blue-800 transition-colors">
            <PlusCircle className="w-4 h-4" /> Submit New Project
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-blue-50 p-3 rounded-lg"><FileText className="w-6 h-6 text-government-blue" /></div>
          <div>
            <div className="text-2xl font-bold text-black">14</div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Total Submissions (MTD)</div>
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-amber-50 p-3 rounded-lg"><Clock className="w-6 h-6 text-amber-600" /></div>
          <div>
            <div className="text-2xl font-bold text-black">6</div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Pending Review</div>
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-green-50 p-3 rounded-lg"><CheckCircle className="w-6 h-6 text-green-600" /></div>
          <div>
            <div className="text-2xl font-bold text-black">5</div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Approved</div>
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="bg-red-50 p-3 rounded-lg"><XCircle className="w-6 h-6 text-red-600" /></div>
          <div>
            <div className="text-2xl font-bold text-black">3</div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Returned</div>
          </div>
        </div>
      </div>

      {/* Submissions List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h3 className="font-bold text-black">Recent Submissions</h3>
          <div className="flex gap-2">
            <select className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm text-slate-700">
              <option>All Statuses</option>
              <option>Pending Review</option>
              <option>Under Evaluation</option>
              <option>Approved</option>
              <option>Returned</option>
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-white border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-semibold text-slate-700">Ref ID / Project Name</th>
                <th className="px-6 py-4 font-semibold text-slate-700">Ministry & Submitter</th>
                <th className="px-6 py-4 font-semibold text-slate-700">Submission Date</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-right">Est. Cost (₹ Cr)</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-center">Status</th>
                <th className="px-6 py-4 font-semibold text-slate-700 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {newProjects.map((project) => (
                <tr key={project.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-bold text-government-blue text-xs">{project.id}</div>
                    <div className="text-black font-medium mt-0.5">{project.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-800">{project.ministry}</div>
                    <div className="text-slate-500 text-xs mt-0.5">{project.submittedBy}</div>
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    {project.date}
                  </td>
                  <td className="px-6 py-4 text-right font-medium text-slate-800">
                    {project.cost.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${
                      project.status === 'Approved' ? 'bg-green-100 text-green-800' :
                      project.status === 'Pending Review' ? 'bg-amber-100 text-amber-800' :
                      project.status === 'Returned for Clarification' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-government-blue hover:text-blue-800 text-xs font-semibold inline-flex items-center">
                      Review <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </button>
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

export default NewProjectsView;
