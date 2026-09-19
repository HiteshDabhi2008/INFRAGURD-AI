import React, { useState, useEffect, useMemo } from 'react';
import { 
  FileText, 
  Download, 
  Copy, 
  Printer, 
  Sparkles, 
  Loader2, 
  CheckCircle, 
  AlertTriangle, 
  FolderKanban, 
  ShieldCheck, 
  Layers, 
  RefreshCw
} from 'lucide-react';
import { reportsApi, projectApi } from '../../services/api';
import type { PortfolioData, GeneratedReport, ProjectSummary } from '../../services/api';

// Custom lightweight Markdown renderer to support headings, tables, bold text, lists, and callouts
const MarkdownDocumentViewer: React.FC<{ markdown: string }> = ({ markdown }) => {
  const renderedElements = useMemo(() => {
    if (!markdown) return null;
    const lines = markdown.split('\n');
    const elements: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      // Empty line
      if (!line.trim()) {
        i++;
        continue;
      }

      // Heading 1
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={`h1-${i}`} className="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-3 mt-6 mb-4 tracking-tight">
            {line.replace(/^#\s+/, '')}
          </h1>
        );
        i++;
        continue;
      }

      // Heading 2
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${i}`} className="text-lg font-bold text-government-blue flex items-center gap-2 mt-6 mb-3 pt-2">
            <span className="w-1.5 h-4 bg-government-blue rounded-sm inline-block" />
            {line.replace(/^##\s+/, '')}
          </h2>
        );
        i++;
        continue;
      }

      // Heading 3
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${i}`} className="text-base font-semibold text-slate-800 mt-4 mb-2">
            {line.replace(/^###\s+/, '')}
          </h3>
        );
        i++;
        continue;
      }

      // Horizontal Rule
      if (line.trim() === '---' || line.trim() === '***') {
        elements.push(<hr key={`hr-${i}`} className="my-6 border-slate-200" />);
        i++;
        continue;
      }

      // Table parsing
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        const tableLines: string[] = [];
        while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
          tableLines.push(lines[i].trim());
          i++;
        }

        if (tableLines.length >= 2) {
          const headerCells = tableLines[0]
            .slice(1, -1)
            .split('|')
            .map((c) => c.trim());
          // Skip divider line (line index 1)
          const dataRows = tableLines.slice(2).map((r) =>
            r
              .slice(1, -1)
              .split('|')
              .map((c) => c.trim())
          );

          elements.push(
            <div key={`table-${i}`} className="my-4 overflow-x-auto rounded-lg border border-slate-200 shadow-sm">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-slate-100/80 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
                  <tr>
                    {headerCells.map((h, colIdx) => (
                      <th key={colIdx} className="px-4 py-2.5">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {dataRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50/80 transition-colors">
                      {row.map((cell, cIdx) => {
                        const isRisk = cell === 'CRITICAL' || cell === 'HIGH' || cell === 'MEDIUM' || cell === 'LOW';
                        return (
                          <td key={cIdx} className="px-4 py-2 text-slate-700 font-medium">
                            {isRisk ? (
                              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                                cell === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                                cell === 'HIGH' ? 'bg-amber-100 text-amber-800' :
                                cell === 'MEDIUM' ? 'bg-blue-100 text-blue-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {cell}
                              </span>
                            ) : (
                              cell
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          continue;
        }
      }

      // Unordered list item
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const bulletText = line.trim().replace(/^[-*]\s+/, '');
        elements.push(
          <div key={`li-${i}`} className="flex items-start gap-2 my-1.5 text-sm text-slate-700">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-2 shrink-0" />
            <span dangerouslySetInnerHTML={{ __html: formatInline(bulletText) }} />
          </div>
        );
        i++;
        continue;
      }

      // Callout / Note line (e.g. *(Note: ...)* )
      if (line.trim().startsWith('*(') && line.trim().endsWith(')*')) {
        elements.push(
          <div key={`note-${i}`} className="my-3 p-3 bg-amber-50/80 border border-amber-200 rounded-lg text-xs text-amber-900 italic">
            {line.trim().replace(/^\*\(/, '').replace(/\)\*$/, '')}
          </div>
        );
        i++;
        continue;
      }

      // Standard paragraph
      elements.push(
        <p key={`p-${i}`} className="text-sm leading-relaxed text-slate-700 my-2.5" dangerouslySetInnerHTML={{ __html: formatInline(line) }} />
      );
      i++;
    }

    return elements;
  }, [markdown]);

  return <div className="space-y-1">{renderedElements}</div>;
};

// Simple inline formatter for bold and italics
function formatInline(text: string): string {
  let res = text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="text-slate-600">$1</em>');
  return res;
}

const ReportsView: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportType, setReportType] = useState<string>('portfolio_overview');
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [projectOptions, setProjectOptions] = useState<ProjectSummary[]>([]);
  const [activeReport, setActiveReport] = useState<GeneratedReport | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  // Load portfolio KPI summary & candidate projects
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoadingData(true);
      setError('');
      const [pRes, listRes] = await Promise.all([
        reportsApi.getPortfolioData(),
        projectApi.list({ limit: 100 })
      ]);
      setPortfolioData(pRes.data);
      if (listRes.data && listRes.data.projects) {
        setProjectOptions(listRes.data.projects);
        if (listRes.data.projects.length > 0) {
          setSelectedProject(listRes.data.projects[0].project_code);
        }
      }
    } catch (err: any) {
      console.error('Failed to load portfolio reports data', err);
      setError(err?.response?.data?.detail || 'Failed to initialize portfolio intelligence.');
    } finally {
      setLoadingData(false);
    }
  };

  const handleGenerateReport = async (typeToGenerate = reportType) => {
    try {
      setGenerating(true);
      setError('');
      const payload: { report_type: string; project_code?: string } = {
        report_type: typeToGenerate,
      };
      if (typeToGenerate === 'project_report' && selectedProject) {
        payload.project_code = selectedProject;
      }

      const res = await reportsApi.generate(payload);
      setActiveReport(res.data);
    } catch (err: any) {
      console.error('Report generation error:', err);
      setError(err?.response?.data?.detail || 'Failed to generate authoritative AI report. Please retry.');
    } finally {
      setGenerating(false);
    }
  };

  // Auto-generate default portfolio overview once on initial load if none exists
  useEffect(() => {
    if (!activeReport && !generating && !loadingData && portfolioData) {
      handleGenerateReport('portfolio_overview');
    }
  }, [portfolioData]);

  const copyToClipboard = () => {
    if (!activeReport) return;
    navigator.clipboard.writeText(activeReport.markdown_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  const downloadMarkdown = () => {
    if (!activeReport) return;
    const blob = new Blob([activeReport.markdown_report], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `InfraGuard_Report_${activeReport.report_type}_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const reportButtons = [
    { type: 'portfolio_overview', label: 'Portfolio Overview', desc: '8-Part Executive Dossier' },
    { type: 'state_wise', label: 'State-wise Analysis', desc: 'Regional Delay & Progress' },
    { type: 'ministry_wise', label: 'Ministry Review', desc: 'Central Implementation Outlay' },
    { type: 'risk_overview', label: 'Risk Intelligence', desc: 'Early Warnings & Overruns' },
    { type: 'project_report', label: 'Project Performance', desc: 'Single-Project Audit' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm print:hidden">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Project Reports</h1>
            <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-800 text-xs font-semibold rounded-full border border-emerald-200 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              MoSPI Verified
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Authoritative, fact-grounded portfolio briefings generated with live MoSPI IPMD metrics and zero hallucination.
          </p>
        </div>

        <button
          onClick={loadInitialData}
          disabled={loadingData || generating}
          className="flex items-center gap-2 px-3.5 py-2 text-slate-600 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-100 transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loadingData ? 'animate-spin text-government-blue' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Portfolio KPI Summary Strip */}
      {portfolioData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 print:hidden">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="p-3 bg-blue-50 text-government-blue rounded-lg border border-blue-100">
              <FolderKanban className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-900">{portfolioData.total_projects.toLocaleString()}</div>
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Authorized Projects</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="p-3 bg-teal-50 text-teal-700 rounded-lg border border-teal-100">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-900">{portfolioData.average_progress}%</div>
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Average Progress</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="p-3 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-900">
                ₹{(portfolioData.financial.revised_cost || portfolioData.financial.original_cost || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} Cr
              </div>
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total Revised Outlay</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="p-3 bg-rose-50 text-rose-700 rounded-lg border border-rose-100">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xl font-bold text-rose-700">
                {(portfolioData.risk_distribution.CRITICAL || 0) + (portfolioData.risk_distribution.HIGH || 0)}
              </div>
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Critical & High Risk</div>
            </div>
          </div>
        </div>
      )}

      {/* Report Generator Controls */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 print:hidden space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-government-blue" />
            <h2 className="font-bold text-slate-900 text-base">Select Report Template & Scope</h2>
          </div>
          <span className="text-xs text-slate-400 font-medium">Model: Groq Llama 3 / Deterministic Fallback</span>
        </div>

        {/* Report Type Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {reportButtons.map((btn) => (
            <button
              key={btn.type}
              onClick={() => {
                setReportType(btn.type);
                if (btn.type !== 'project_report') {
                  handleGenerateReport(btn.type);
                }
              }}
              className={`text-left p-3 rounded-lg border transition-all ${
                reportType === btn.type
                  ? 'border-government-blue bg-blue-50/70 text-government-blue ring-2 ring-government-blue/20'
                  : 'border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700'
              }`}
            >
              <div className="font-semibold text-xs leading-snug">{btn.label}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">{btn.desc}</div>
            </button>
          ))}
        </div>

        {/* Project Dropdown for Single Project Report */}
        {reportType === 'project_report' && (
          <div className="pt-2 flex flex-col sm:flex-row gap-3 items-end">
            <div className="w-full sm:flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select Infrastructure Project for Audit:
              </label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-government-blue"
              >
                {projectOptions.map((p) => (
                  <option key={p.project_code} value={p.project_code}>
                    {p.project_code} — {p.project_name.slice(0, 65)} ({p.state || 'India'})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => handleGenerateReport('project_report')}
              disabled={generating || !selectedProject}
              className="w-full sm:w-auto px-5 py-2 bg-government-blue text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors flex items-center justify-center gap-2"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>Generate Project Dossier</span>
            </button>
          </div>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="bg-rose-50 border border-rose-300 rounded-xl p-4 flex items-center gap-3 text-rose-800 text-sm print:hidden">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Viewer Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Document Action Bar */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 print:hidden">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              {activeReport ? `Generated: ${activeReport.report_type.replace('_', ' ')}` : 'Report Preview'}
            </span>
            {activeReport?.metadata?.generated_at && (
              <span className="text-xs text-slate-400">({activeReport.metadata.generated_at})</span>
            )}
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={copyToClipboard}
              disabled={!activeReport || generating}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-100 transition-colors shadow-xs"
            >
              {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy Markdown'}</span>
            </button>

            <button
              onClick={downloadMarkdown}
              disabled={!activeReport || generating}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-100 transition-colors shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download .md</span>
            </button>

            <button
              onClick={handlePrint}
              disabled={!activeReport || generating}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-government-blue rounded-md hover:bg-blue-800 transition-colors shadow-xs"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Export PDF</span>
            </button>
          </div>
        </div>

        {/* Document Body */}
        <div className="p-8 sm:p-12 min-h-[500px]">
          {generating ? (
            <div className="py-28 flex flex-col items-center justify-center space-y-4 text-center">
              <Loader2 className="w-10 h-10 animate-spin text-government-blue" />
              <div>
                <h4 className="text-base font-bold text-slate-800">Synthesizing Official Executive Report</h4>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                  Retrieving real-time authorized database telemetry across states, sectors, and ministries...
                </p>
              </div>
            </div>
          ) : activeReport ? (
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Government Header Stamp */}
              <div className="border-b-2 border-slate-900 pb-6">
                {/* Tricolor bar */}
                <div className="flex h-1.5 w-full rounded-full overflow-hidden mb-5">
                  <div className="flex-1 bg-[#FF9933]" />
                  <div className="flex-1 bg-white border-y border-slate-200" />
                  <div className="flex-1 bg-[#138808]" />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[11px] font-bold tracking-widest text-slate-500 uppercase">
                      Government of India • Ministry of Statistics & Programme Implementation
                    </div>
                    <div className="text-lg font-extrabold text-slate-900 tracking-tight mt-0.5">
                      Infrastructure and Project Monitoring Division (IPMD)
                    </div>
                    <div className="text-xs text-slate-600 mt-0.5 font-medium">
                      InfraGuard-AI Central Portfolio Intelligence Briefing
                    </div>
                  </div>

                  <div className="text-right hidden sm:block">
                    <div className="text-xs font-mono font-bold text-slate-700">
                      REF: IPMD/RPT/{new Date().getFullYear()}/{Math.floor(1000 + Math.random() * 9000)}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Classification: Official / Internal
                    </div>
                  </div>
                </div>
              </div>

              {/* Rendered Markdown */}
              <div className="prose max-w-none text-slate-800">
                <MarkdownDocumentViewer markdown={activeReport.markdown_report} />
              </div>

              {/* Metadata & Verification Seal */}
              <div className="mt-12 pt-6 border-t border-slate-200 bg-slate-50 p-5 rounded-xl text-xs text-slate-600 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2 font-semibold text-slate-800">
                  <div className="flex items-center gap-1.5 text-emerald-700">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>VERIFIED GROUNDED DATASET (MoSPI IPMD REPOSITORY)</span>
                  </div>
                  <div>Generated For: {activeReport.metadata.generated_for}</div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-slate-500 pt-1">
                  <div>
                    <span className="font-medium text-slate-700">Projects Covered:</span> {activeReport.metadata.projects_covered}
                  </div>
                  <div>
                    <span className="font-medium text-slate-700">Authority:</span> {activeReport.metadata.reporting_authority}
                  </div>
                  <div>
                    <span className="font-medium text-slate-700">Generated:</span> {activeReport.metadata.generated_at}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-400">
              <FileText className="w-12 h-12 mx-auto text-slate-300 mb-3" />
              <h4 className="text-base font-semibold text-slate-700">No report generated yet</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                Select a report template above and click generate to synthesize grounded portfolio intelligence.
              </p>
              <button
                onClick={() => handleGenerateReport('portfolio_overview')}
                className="px-4 py-2 bg-government-blue text-white rounded-lg text-xs font-semibold hover:bg-blue-800 transition-colors"
              >
                Generate Executive Overview
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsView;
