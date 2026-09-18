import { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import { scaleQuantize } from 'd3-scale';
import { Map, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../services/api';

const INDIA_TOPO_JSON = "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/india/india-states.json";

interface StateData {
  name: string;
  project_count: number;
  original_cost: number;
  revised_cost: number;
  expenditure: number;
  average_progress: number;
  high_risk_count: number;
  critical_count: number;
}

const colorScale = scaleQuantize<string>()
  .domain([0, 100])
  .range([
    "#e0f2fe",
    "#bae6fd",
    "#7dd3fc",
    "#38bdf8",
    "#0ea5e9",
    "#0284c7",
    "#0369a1",
    "#075985"
  ]);

const StateView = () => {
  const [tooltipContent, setTooltipContent] = useState("");
  const [stateData, setStateData] = useState<StateData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.state().then((res) => {
      setStateData(res.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading state analysis...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black">State-wise Infrastructure</h1>
          <p className="text-sm text-slate-500">Geospatial analysis of project distribution and risk</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Map Visualization */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-2 relative">
          <h3 className="text-lg font-bold text-black mb-2 flex items-center gap-2">
            <Map className="w-5 h-5 text-government-blue" /> Infrastructure Heatmap
          </h3>
          <p className="text-sm text-slate-500 mb-6">Showing concentration of high-value projects</p>
          
          <div className="bg-slate-50 rounded-lg border border-slate-100 h-[500px] flex items-center justify-center overflow-hidden">
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{
                scale: 850,
                center: [80, 22] // Centered on India
              }}
              className="w-full h-full"
            >
              <Geographies geography={INDIA_TOPO_JSON}>
                {({ geographies }) => {
                  const maxProjects = Math.max(...stateData.map(s => s.project_count), 1);
                  return geographies.map(geo => {
                    const stateName = geo?.properties?.NAME_1 || geo?.properties?.name;
                    const cur = stateData.find(s => {
                      return stateName && (
                        stateName.includes(s.name) || s.name.includes(stateName)
                      );
                    });
                    
                    const heatValue = cur ? (cur.project_count / maxProjects) * 100 : 0;
                    
                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        fill={cur ? colorScale(heatValue) : "#f1f5f9"}
                        stroke="#cbd5e1"
                        strokeWidth={0.5}
                        onMouseEnter={() => {
                          if (cur) {
                            setTooltipContent(`${cur.name}: ${cur.project_count} Projects (₹${Math.round(cur.expenditure).toLocaleString()} Cr)`);
                          } else {
                            setTooltipContent(stateName || "No data");
                          }
                        }}
                        onMouseLeave={() => {
                          setTooltipContent("");
                        }}
                        style={{
                          default: { outline: "none" },
                          hover: { fill: "#f59e0b", outline: "none", cursor: "pointer" },
                          pressed: { fill: "#d97706", outline: "none" }
                        } as any}
                      />
                    );
                  });
                }}
              </Geographies>
            </ComposableMap>
            
            {/* Custom Tooltip */}
            {tooltipContent && (
              <div className="absolute top-20 right-8 bg-slate-900 text-white text-xs px-3 py-2 rounded-md shadow-lg font-medium pointer-events-none">
                {tooltipContent}
              </div>
            )}
          </div>
        </div>

        {/* State Highlights */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-black mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" /> High Attention States
            </h3>
            
            <div className="space-y-4">
              {stateData.filter(s => s.high_risk_count > 0 || s.critical_count > 0).sort((a,b) => (b.high_risk_count + b.critical_count) - (a.high_risk_count + a.critical_count)).slice(0, 4).map((state, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50 flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-black">{state.name}</span>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                      state.critical_count > 0 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {state.critical_count > 0 ? 'CRITICAL RISK' : 'HIGH RISK'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Active Projects:</span>
                    <span className="font-semibold text-slate-700">{state.project_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Total Exp:</span>
                    <span className="font-semibold text-slate-700">₹{Math.round(state.expenditure).toLocaleString()} Cr</span>
                  </div>
                </div>
              ))}
            </div>
            
            <Link to="/dashboard/projects" className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors">
              View All State Data <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
};

export default StateView;
