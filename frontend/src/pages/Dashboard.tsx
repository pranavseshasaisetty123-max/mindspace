import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, api } from '../contexts/AuthContext';
import { DashboardLoader } from '../components/SkeletonLoaders';
import { Brain, LogOut, Sparkles, BookOpen, PenLine, Flame, ShieldAlert, RotateCcw } from 'lucide-react';

interface Journal {
  id: number;
  mood: number;
  content: string;
  created_at: string;
}

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [greeting, setGreeting] = useState("Hello");
  const [loading, setLoading] = useState(true);
  const [streak, setStreak] = useState(0);
  const [moodAvg, setMoodAvg] = useState<number | null>(null);
  const [reflectionScore, setReflectionScore] = useState(0);
  const [recentJournals, setRecentJournals] = useState<Journal[]>([]);
  const [error, setError] = useState<boolean>(false);
  const [retryCount, setRetryCount] = useState<number>(0);

  // Calculate dynamic greeting based on system hours
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  // Fetch journals to compute statistics dynamically
  useEffect(() => {
    setLoading(true);
    setError(false);
    api.get('/api/v1/journals?limit=100')
      .then((res) => {
        const journals: Journal[] = res.data;
        setRecentJournals(journals.slice(0, 2)); // Show top 2 recents
        
        if (journals.length === 0) {
          setStreak(0);
          setMoodAvg(null);
          setReflectionScore(0);
          return;
        }

        // 1. Calculate Mood Average
        const totalMood = journals.reduce((sum, j) => sum + j.mood, 0);
        setMoodAvg(Number((totalMood / journals.length).toFixed(1)));

        // 2. Calculate Writing Streak (consecutive calendar days)
        const uniqueDates = new Set(
          journals.map(j => new Date(j.created_at).toDateString())
        );
        let currentStreak = 0;
        const today = new Date();
        const checkDate = new Date();

        while (true) {
          if (uniqueDates.has(checkDate.toDateString())) {
            currentStreak++;
            checkDate.setDate(checkDate.getDate() - 1);
          } else {
            if (currentStreak === 0 && checkDate.toDateString() === today.toDateString()) {
              checkDate.setDate(checkDate.getDate() - 1);
              continue;
            }
            break;
          }
        }
        setStreak(currentStreak);

        // 3. Compute Reflection Score (0 to 100)
        const last7Days = new Set(
          Array.from({ length: 7 }, (_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - i);
            return d.toDateString();
          })
        );
        const daysWrittenInLast7 = Array.from(uniqueDates).filter(d => last7Days.has(d)).length;
        const consistencyScore = (daysWrittenInLast7 / 7) * 100;

        const avgWordCount = journals.reduce((sum, j) => sum + j.content.trim().split(/\s+/).length, 0) / journals.length;
        const depthScore = Math.min((avgWordCount / 150) * 100, 100);

        setReflectionScore(Math.round((consistencyScore * 0.4) + (depthScore * 0.6)));
      })
      .catch((err) => {
        console.error("Failed to compile dashboard metrics:", err);
        setError(true);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [retryCount]);

  // Format today's date for hero segment
  const todayFormatted = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });

  const userDisplayName = user?.email ? user.email.split('@')[0] : 'Writer';

  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col font-sans">
      
      {/* Top Premium Navbar */}
      <nav className="sticky top-0 z-50 bg-darkcard/80 backdrop-blur-md border-b border-darkborder h-16 flex items-center justify-between px-6 md:px-12">
        <div className="flex items-center space-x-2 text-indigo-400">
          <Brain className="h-6 w-6 animate-pulse" />
          <span className="text-lg font-bold tracking-wider text-gray-100">MindSpace</span>
        </div>
        
        <div className="flex items-center space-x-6">
          <Link to="/" className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition-colors border-b-2 border-indigo-500 pb-1.5 pt-1">
            Dashboard
          </Link>
          <Link to="/timeline" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1">
            Timeline
          </Link>
          <Link to="/analytics" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1">
            Analytics
          </Link>
          <Link to="/settings" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1">
            Settings
          </Link>
          <Link to="/journal/new" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1 flex items-center space-x-1">
            <PenLine className="h-4 w-4" />
            <span>Write</span>
          </Link>
        </div>

        <div className="flex items-center space-x-4">
          <span className="hidden md:inline text-xs text-gray-500 font-semibold max-w-[120px] truncate">{user?.email}</span>
          <button
            onClick={logout}
            className="flex items-center space-x-1.5 px-3 py-1.5 border border-darkborder hover:border-red-500/20 text-xs font-semibold rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-950/10 transition-all duration-300 transform active:scale-95"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </nav>

      {/* Main Focus Container */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12 space-y-12 animate-fade-in">
        
        {error ? (
          <div className="bg-red-950/20 border border-red-500/20 rounded-2xl p-8 text-center space-y-4 max-w-md mx-auto my-12">
            <div className="flex justify-center text-red-400">
              <ShieldAlert className="h-10 w-10 animate-bounce" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-gray-200">Failed to Retrieve Metrics</h3>
              <p className="text-xs text-gray-500 font-light">The API service could not load your journal data.</p>
            </div>
            <button
              onClick={() => setRetryCount(prev => prev + 1)}
              className="inline-flex items-center space-x-1.5 bg-red-950/60 hover:bg-red-950/90 text-red-300 font-bold py-2 px-5 border border-red-500/30 rounded-xl text-xs transition-colors btn-premium focus:outline-none"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Retry Load</span>
            </button>
          </div>
        ) : loading ? (
          <DashboardLoader />
        ) : (
          <>
            {/* Minimal Greeting Hero Section */}
            <div className="space-y-6 text-center md:text-left">
              <div>
                <span className="text-xs text-gray-500 uppercase tracking-widest font-bold">{todayFormatted}</span>
                <h2 className="text-4xl font-extrabold text-gray-100 mt-2 tracking-tight">
                  {greeting}, {userDisplayName} 👋
                </h2>
                <p className="text-lg text-gray-400 mt-2 font-light">What's on your mind today?</p>
              </div>

              {/* Central Premium CTA Card */}
              <div className="bg-gradient-to-br from-indigo-950/20 via-indigo-900/10 to-transparent border border-indigo-500/10 rounded-2xl p-8 flex flex-col md:flex-row justify-between items-center gap-6 shadow-md hover:border-indigo-500/20 transition-all duration-300">
                <div className="space-y-2 text-center md:text-left">
                  <h3 className="text-md font-bold text-gray-200">Start a new reflection</h3>
                  <p className="text-xs text-gray-400 leading-relaxed max-w-md">
                    Take a moment to step away, write freely, and track your sleep, energy, and stress metrics.
                  </p>
                </div>
                
                <button
                  onClick={() => navigate('/journal/new')}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3.5 px-8 rounded-xl transition-all duration-300 transform hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/20 flex items-center space-x-2 shrink-0 btn-premium"
                >
                  <BookOpen className="h-5 w-5" />
                  <span>Write Reflection</span>
                </button>
              </div>
            </div>

            {/* Streak & Date quick panel */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-darkcard border border-darkborder rounded-2xl px-6 py-4 shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="h-9 w-9 bg-indigo-500/10 border border-indigo-500/20 rounded-full flex items-center justify-center">
                  <Flame className="h-5 w-5 text-indigo-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Current Writing Streak</p>
                  <p className="text-sm font-bold text-indigo-400">{streak} {streak === 1 ? 'day' : 'days'}</p>
                </div>
              </div>
              
              <div className="h-6 w-px bg-darkborder hidden sm:block"></div>
              
              <div className="text-center sm:text-right">
                <p className="text-xs text-gray-500 font-medium">Session logs</p>
                <Link to="/timeline" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
                  Browse timeline database →
                </Link>
              </div>
            </div>

            {/* Recent Reflections Previews */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold tracking-widest text-gray-500 uppercase">Recent Reflections</h3>
                {recentJournals.length > 0 && (
                  <Link to="/timeline" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                    View timeline history
                  </Link>
                )}
              </div>

              {recentJournals.length === 0 ? (
                <div className="border border-dashed border-darkborder rounded-2xl h-48 flex flex-col items-center justify-center p-6 text-center bg-darkcard/30">
                  <BookOpen className="h-8 w-8 text-gray-600 mb-3" />
                  <p className="font-semibold text-gray-300 text-sm">Every meaningful journey begins with a single reflection.</p>
                  <p className="text-xs text-gray-500 mt-1.5">Write your first journal to begin your story.</p>
                  <button
                    onClick={() => navigate('/journal/new')}
                    className="mt-5 bg-indigo-950/40 hover:bg-indigo-900/30 border border-indigo-500/20 text-indigo-300 text-xs px-5 py-2.5 rounded-xl transition-all duration-300 transform active:scale-95"
                  >
                    Draft First Entry
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {recentJournals.map((journal) => (
                    <div 
                      key={journal.id}
                      onClick={() => navigate(`/journal/${journal.id}`)}
                      className="group bg-darkcard border border-darkborder hover:border-indigo-500/30 rounded-2xl p-6 shadow-sm hover:shadow-md cursor-pointer transition-all duration-300 flex flex-col justify-between min-h-[160px]"
                    >
                      <div>
                        <div className="flex justify-between items-center text-[10px] text-gray-500 font-semibold uppercase">
                          <span>{new Date(journal.created_at).toLocaleDateString()}</span>
                          <span className="bg-indigo-950/40 border border-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full">
                            Mood: {journal.mood}
                          </span>
                        </div>
                        <h4 className="text-md font-bold text-gray-200 mt-3 group-hover:text-indigo-400 transition-colors line-clamp-1">
                          {journal.content.trim().split('\n')[0].replace(/^#\s*/, '') || 'Untitled Entry'}
                        </h4>
                        <p className="text-xs text-gray-400 mt-2 line-clamp-2 leading-relaxed">
                          {journal.content.replace(/^#.*\n?/, '').substring(0, 120)}
                        </p>
                      </div>
                      <span className="text-[10px] text-indigo-400/60 font-semibold mt-4 group-hover:text-indigo-400 transition-colors">
                        Edit entry →
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Relocated Analytics Lower */}
            <div className="pt-6 border-t border-darkborder space-y-4">
              <h3 className="text-xs font-bold tracking-widest text-gray-500 uppercase">Secondary Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                <div className="bg-darkcard border border-darkborder/50 rounded-2xl p-5 shadow-sm">
                  <p className="text-xs font-medium text-gray-500 uppercase">Mood Average</p>
                  <p className="text-2xl font-bold text-gray-200 mt-2">{moodAvg !== null ? `${moodAvg} / 5.0` : '--'}</p>
                  <p className="text-[10px] text-gray-500 mt-1">Average mood score logged</p>
                </div>

                <div className="bg-darkcard border border-darkborder/50 rounded-2xl p-5 shadow-sm">
                  <p className="text-xs font-medium text-gray-500 uppercase">Depth Index</p>
                  <p className="text-2xl font-bold text-gray-200 mt-2">{reflectionScore} / 100</p>
                  <p className="text-[10px] text-gray-500 mt-1">Based on consistency & depth</p>
                </div>

                <div className="bg-darkcard border border-darkborder/50 rounded-2xl p-5 shadow-sm flex flex-col justify-center">
                  <div className="flex items-center space-x-2 text-[10px] text-indigo-400">
                    <Sparkles className="h-4 w-4" />
                    <span className="font-semibold uppercase tracking-wider">AI Insights (Sprint 3)</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                    Trigger summary patterns and diagnostic guardrails live next sprint.
                  </p>
                </div>

              </div>
            </div>
            
            {/* Companion Warning Footer segment */}
            <div className="flex items-center justify-center space-x-2 text-[10px] text-gray-600 bg-darkcard/20 border border-darkborder/50 rounded-xl p-3">
              <ShieldAlert className="h-4 w-4 text-gray-500 shrink-0" />
              <span>MindSpace is a reflective journal log. It is not an alternative to therapeutic care or clinical diagnostics.</span>
            </div>
          </>
        )}
      </main>
    </div>
  );
};
