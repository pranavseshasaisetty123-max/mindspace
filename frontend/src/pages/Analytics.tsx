import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, api } from '../contexts/AuthContext';
import { SummaryCards } from '../components/SummaryCards';
import { TrendLineChart } from '../components/TrendLineChart';
import { TagPieChart } from '../components/TagPieChart';
import { AnalyticsLoader } from '../components/SkeletonLoaders';
import { 
  Brain, 
  LogOut, 
  TrendingUp, 
  BarChart2, 
  Clock, 
  Sparkles, 
  Compass,
  Smile,
  Zap,
  Activity,
  ChevronRight
} from 'lucide-react';

interface TrendData {
  date: string;
  avg_mood: number;
  avg_stress: number;
  avg_energy: number;
  avg_sleep: number;
}

interface TagCount {
  tag: string;
  count: number;
}

interface RecentReflection {
  journal_id: number;
  title: string;
  summary: string;
  reflection_question: string;
}

interface SummaryData {
  total_reflections: number;
  streak_days: number;
  average_mood: number;
  average_sleep: number;
}

interface AnalyticsDashboardData {
  summary: SummaryData;
  trends: TrendData[];
  tag_distribution: TagCount[];
  recent_reflections: RecentReflection[];
}

type MetricType = 'avg_mood' | 'avg_stress' | 'avg_energy' | 'avg_sleep';

export const Analytics: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [daysLimit, setDaysLimit] = useState<number>(30);
  const [interval, setInterval] = useState<string>('daily');
  const [activeMetric, setActiveMetric] = useState<MetricType>('avg_mood');

  // Trigger data fetches when parameters are adjusted
  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const response = await api.get(
          `/api/v1/analytics/dashboard?days_limit=${daysLimit}&interval=${interval}`
        );
        setData(response.data);
      } catch (err) {
        console.error('Failed to load dashboard aggregates:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [daysLimit, interval]);

  const handleLogoutClick = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Premium Dashboard Header Nav block */}
      <header className="border-b border-darkborder/50 bg-darkcard/50 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-2.5 focus:outline-none">
          <div className="bg-indigo-600/10 border border-indigo-500/20 p-2 rounded-xl">
            <Brain className="h-5 w-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-sm font-black tracking-tight text-gray-200 uppercase">MindSpace</h1>
            <p className="text-[9px] text-indigo-400/80 font-bold uppercase tracking-wider -mt-0.5">AI Journal</p>
          </div>
        </Link>

        {/* Mid navigation links */}
        <nav className="hidden md:flex items-center space-x-1.5 bg-darkbg border border-darkborder/50 rounded-full px-2 py-1">
          <Link 
            to="/" 
            className="text-xs text-gray-400 hover:text-gray-200 px-4 py-1.5 rounded-full transition-colors font-medium"
          >
            Dashboard
          </Link>
          <Link 
            to="/timeline" 
            className="text-xs text-gray-400 hover:text-gray-200 px-4 py-1.5 rounded-full transition-colors font-medium"
          >
            Timeline
          </Link>
          <Link 
            to="/analytics" 
            className="bg-indigo-950/40 text-indigo-300 border border-indigo-500/20 text-xs px-4 py-1.5 rounded-full transition-colors font-semibold"
          >
            Analytics
          </Link>
          <Link 
            to="/settings" 
            className="text-xs text-gray-400 hover:text-gray-200 px-4 py-1.5 rounded-full transition-colors font-medium"
          >
            Settings
          </Link>
        </nav>

        {/* Right action tools */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:block text-right">
            <p className="text-xs font-semibold text-gray-300">{user?.email}</p>
            <p className="text-[10px] text-gray-500">MindSpace Member</p>
          </div>
          <button
            onClick={handleLogoutClick}
            className="bg-darkbg hover:bg-darkborder/30 border border-darkborder/60 hover:text-red-400 text-gray-400 p-2.5 rounded-xl transition-all focus:outline-none"
            title="Logout Session"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Main dashboard core content viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-8 min-w-0">
        
        {/* Banner Title & filter header deck */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-darkborder/30 pb-6">
          <div>
            <h2 className="text-2xl font-black text-gray-100 flex items-center space-x-2">
              <TrendingUp className="h-6 w-6 text-indigo-400 shrink-0" />
              <span>Reflective Insights</span>
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              Visualize emotional indicators, sleep behaviors, and metadata distributions.
            </p>
          </div>

          {/* Quick filter selection switches */}
          <div className="flex items-center space-x-2 shrink-0">
            <select
              value={daysLimit}
              onChange={(e) => setDaysLimit(parseInt(e.target.value))}
              className="bg-darkcard border border-darkborder rounded-xl px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-indigo-500/40 font-semibold"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
              <option value={365}>Last Year</option>
              <option value={0}>All Time</option>
            </select>

            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="bg-darkcard border border-darkborder rounded-xl px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-indigo-500/40 font-semibold"
            >
              <option value="daily">Daily Binning</option>
              <option value="weekly">Weekly Binning</option>
              <option value="monthly">Monthly Binning</option>
            </select>
          </div>
        </div>

        {/* Dynamic viewport renderer checks */}
        {loading ? (
          <AnalyticsLoader />
        ) : !data || data.summary.total_reflections === 0 ? (
          <div className="bg-darkcard border border-darkborder rounded-2xl p-12 text-center max-w-md mx-auto space-y-4 shadow-sm my-12">
            <div className="bg-indigo-950/20 border border-indigo-500/20 w-12 h-12 rounded-2xl flex items-center justify-center mx-auto">
              <BarChart2 className="h-6 w-6 text-indigo-400" />
            </div>
            <h3 className="text-sm font-bold text-gray-200">No journals found to compile analytics</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Write a few daily journal entries and save AI reflection insights to generate statistics graphs.
            </p>
            <Link
              to="/"
              className="inline-block bg-indigo-950/40 border border-indigo-500/20 hover:bg-indigo-900/40 text-indigo-300 font-semibold px-6 py-2 rounded-xl text-xs transition-colors btn-premium"
            >
              Write First Entry
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* KPI Metric cards */}
            <SummaryCards summary={data.summary} />

            {/* Line graphs and toggle tab selectors */}
            <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-darkborder/60 pb-4">
                <div className="flex items-center space-x-2">
                  <Activity className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Indicators timeline</span>
                </div>
                
                {/* Metric Swapper Tabs deck */}
                <div className="flex flex-wrap gap-1 bg-darkbg border border-darkborder/40 rounded-lg p-1">
                  <button
                    onClick={() => setActiveMetric('avg_mood')}
                    className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                      activeMetric === 'avg_mood' 
                        ? 'bg-indigo-950/60 border border-indigo-500/30 text-indigo-300' 
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Smile className="h-3.5 w-3.5" />
                    <span>Mood</span>
                  </button>
                  <button
                    onClick={() => setActiveMetric('avg_stress')}
                    className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                      activeMetric === 'avg_stress' 
                        ? 'bg-indigo-950/60 border border-indigo-500/30 text-indigo-300' 
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Activity className="h-3.5 w-3.5" />
                    <span>Stress</span>
                  </button>
                  <button
                    onClick={() => setActiveMetric('avg_energy')}
                    className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                      activeMetric === 'avg_energy' 
                        ? 'bg-indigo-950/60 border border-indigo-500/30 text-indigo-300' 
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Zap className="h-3.5 w-3.5" />
                    <span>Energy</span>
                  </button>
                  <button
                    onClick={() => setActiveMetric('avg_sleep')}
                    className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                      activeMetric === 'avg_sleep' 
                        ? 'bg-indigo-950/60 border border-indigo-500/30 text-indigo-300' 
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Clock className="h-3.5 w-3.5" />
                    <span>Sleep</span>
                  </button>
                </div>
              </div>

              {/* Aggregation Curve */}
              <TrendLineChart data={data.trends} activeMetric={activeMetric} />
            </div>

            {/* Split row: Left (Tags), Right (Recent AI reflections) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Tags distribution pie chart */}
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm flex flex-col justify-between">
                <div className="border-b border-darkborder/60 pb-3 flex items-center space-x-2">
                  <Compass className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Tag Distribution</span>
                </div>
                <TagPieChart data={data.tag_distribution} />
              </div>

              {/* Recent AI Reflections insights list */}
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm md:col-span-2">
                <div className="border-b border-darkborder/60 pb-3 flex items-center space-x-2">
                  <Sparkles className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Recent Reflections</span>
                </div>

                <div className="space-y-4">
                  {data.recent_reflections.length === 0 ? (
                    <div className="py-8 text-center text-xs text-gray-500 italic">
                      No AI reflections generated yet. Write and analyze entries to view reflections.
                    </div>
                  ) : (
                    data.recent_reflections.map((ref, idx) => (
                      <div 
                        key={idx} 
                        className="bg-darkbg/50 border border-darkborder/50 hover:border-indigo-500/20 p-4 rounded-xl space-y-2.5 transition-colors cursor-pointer group"
                        onClick={() => navigate(`/editor/${ref.journal_id}`)}
                      >
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-gray-200 group-hover:text-indigo-400 transition-colors">
                            {ref.title}
                          </h4>
                          <span className="text-[9px] text-indigo-400 font-bold uppercase tracking-wider flex items-center space-x-0.5">
                            <span>Open entry</span>
                            <ChevronRight className="h-3 w-3" />
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">
                          {ref.summary}
                        </p>
                        <div className="border-t border-darkborder/30 pt-2 text-[10px] italic text-indigo-300/80 leading-relaxed font-serif">
                          Prompt: {ref.reflection_question}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>

          </div>
        )}

      </main>
    </div>
  );
};
