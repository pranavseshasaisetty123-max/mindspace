import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, api } from '../contexts/AuthContext';
import { TimelineLoader } from '../components/SkeletonLoaders';
import { Brain, LogOut, Search, Trash2, Edit3, ChevronDown, ChevronRight, X, SlidersHorizontal, BookOpen, PenLine } from 'lucide-react';

interface TagResponse {
  id: number;
  name: string;
}

interface Journal {
  id: number;
  title: string;
  content: string;
  mood: number;
  stress_level: number;
  energy_level: number;
  sleep_hours: number;
  created_at: string;
  tags: TagResponse[];
}

interface GroupedJournals {
  [year: string]: {
    [month: string]: Journal[];
  };
}

export const Timeline: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  // Data states
  const [journals, setJournals] = useState<Journal[]>([]);
  const [loading, setLoading] = useState(true);
  const [collapsedMonths, setCollapsedMonths] = useState<Record<string, boolean>>({});

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [moodFilter, setMoodFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Pagination states
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const limit = 10; // Load more per page to compile directories nicely

  // Fetch entries
  const fetchJournals = () => {
    setLoading(true);
    let query = `/api/v1/journals?skip=${skip}&limit=${limit + 1}`;
    if (searchTerm.trim()) query += `&search=${encodeURIComponent(searchTerm.trim())}`;
    if (moodFilter) query += `&mood=${moodFilter}`;
    if (tagFilter.trim()) query += `&tag=${encodeURIComponent(tagFilter.trim().toLowerCase())}`;
    
    if (startDate) {
      const startIso = new Date(startDate).toISOString();
      query += `&start_date=${encodeURIComponent(startIso)}`;
    }
    if (endDate) {
      const endIso = new Date(endDate + 'T23:59:59').toISOString();
      query += `&end_date=${encodeURIComponent(endIso)}`;
    }

    api.get(query)
      .then((res) => {
        const data: Journal[] = res.data;
        if (data.length > limit) {
          setHasMore(true);
          setJournals(data.slice(0, limit));
        } else {
          setHasMore(false);
          setJournals(data);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch journal timeline:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Trigger load
  useEffect(() => {
    fetchJournals();
  }, [skip, moodFilter, startDate, endDate]);

  // Handle search submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSkip(0);
    fetchJournals();
  };

  // Clear all filters
  const handleClearFilters = () => {
    setSearchTerm('');
    setMoodFilter('');
    setTagFilter('');
    setStartDate('');
    setEndDate('');
    setSkip(0);
  };

  // Handle soft deletion trigger
  const handleDeleteEntry = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this reflection? (It can be recovered later).")) return;
    try {
      await api.delete(`/api/v1/journals/${id}`);
      fetchJournals();
    } catch (err) {
      console.error("Failed to delete journal entry:", err);
    }
  };

  // Chronological grouping function (Year -> Month)
  const groupEntries = (entries: Journal[]): GroupedJournals => {
    const grouped: GroupedJournals = {};
    entries.forEach((entry) => {
      const date = new Date(entry.created_at);
      const year = date.getFullYear().toString();
      const month = date.toLocaleString('default', { month: 'long' });
      
      if (!grouped[year]) {
        grouped[year] = {};
      }
      if (!grouped[year][month]) {
        grouped[year][month] = [];
      }
      grouped[year][month].push(entry);
    });
    return grouped;
  };

  const groupedJournals = groupEntries(journals);

  // Accordion toggle helper
  const toggleMonth = (yearMonthKey: string) => {
    setCollapsedMonths((prev) => ({
      ...prev,
      [yearMonthKey]: !prev[yearMonthKey]
    }));
  };

  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <nav className="sticky top-0 z-50 bg-darkcard/80 backdrop-blur-md border-b border-darkborder h-16 flex items-center justify-between px-6 md:px-12">
        <div className="flex items-center space-x-2 text-indigo-400">
          <Brain className="h-6 w-6" />
          <span className="text-lg font-bold tracking-wider text-gray-100">MindSpace</span>
        </div>
        
        <div className="flex items-center space-x-6">
          <Link to="/" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1">
            Dashboard
          </Link>
          <span className="text-sm font-semibold text-indigo-400 border-b-2 border-indigo-500 pb-1.5 pt-1">
            Timeline
          </span>
          <Link to="/journal/new" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1 flex items-center space-x-1">
            <PenLine className="h-4 w-4" />
            <span>Write</span>
          </Link>
        </div>

        <button
          onClick={logout}
          className="flex items-center space-x-1.5 px-3 py-1.5 border border-darkborder hover:border-red-500/20 text-xs font-semibold rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-950/10 transition-all duration-300 transform active:scale-95"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </nav>

      {/* Timeline Stream Area */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12 space-y-8 overflow-y-auto">
        
        {/* Large, welcoming header */}
        <div className="space-y-2">
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-100">Your Reflection Timeline</h2>
          <p className="text-sm text-gray-400 font-light">Look back at your personal story, emotional insights, and day tags.</p>
        </div>

        {/* Large Search Bar & Chip dock */}
        <div className="bg-darkcard border border-darkborder rounded-2xl p-5 space-y-4 shadow-sm">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 h-4.5 w-4.5 text-gray-500" />
              <input
                type="text"
                placeholder="Search logs by keyword title or text content..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-xl pl-11 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none placeholder-gray-600"
              />
            </div>
            
            <div className="w-full sm:w-44">
              <input
                type="text"
                placeholder="Filter by #tag"
                value={tagFilter}
                onChange={(e) => setTagFilter(e.target.value)}
                className="w-full bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-xl px-4 py-2.5 text-sm text-gray-200 focus:outline-none placeholder-gray-600"
              />
            </div>
            
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all duration-300 transform active:scale-95 btn-premium shrink-0"
            >
              Filter Entries
            </button>
          </form>

          {/* Refining Dropdown selectors */}
          <div className="flex flex-wrap items-center gap-4 pt-3 border-t border-darkborder/50 text-xs text-gray-400">
            <div className="flex items-center space-x-1.5">
              <SlidersHorizontal className="h-4 w-4 text-gray-500" />
              <span className="font-semibold text-gray-500">Refine:</span>
            </div>

            {/* Mood Dropdown */}
            <div className="flex items-center space-x-1.5">
              <span>Mood:</span>
              <select
                value={moodFilter}
                onChange={(e) => { setMoodFilter(e.target.value); setSkip(0); }}
                className="bg-darkbg border border-darkborder rounded-lg px-2.5 py-1 focus:outline-none text-gray-300"
              >
                <option value="">All</option>
                <option value="5">5 (Vibrant)</option>
                <option value="4">4 (Good)</option>
                <option value="3">3 (Average)</option>
                <option value="2">2 (Low)</option>
                <option value="1">1 (Exhausted)</option>
              </select>
            </div>

            {/* Date Range selectors */}
            <div className="flex items-center space-x-2">
              <span>From:</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => { setStartDate(e.target.value); setSkip(0); }}
                className="bg-darkbg border border-darkborder rounded-lg px-2 py-1 focus:outline-none text-gray-300 text-xs"
              />
              <span>To:</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => { setEndDate(e.target.value); setSkip(0); }}
                className="bg-darkbg border border-darkborder rounded-lg px-2 py-1 focus:outline-none text-gray-300 text-xs"
              />
            </div>

            {/* Clear Button */}
            {(searchTerm || moodFilter || tagFilter || startDate || endDate) && (
              <button
                onClick={handleClearFilters}
                className="ml-auto text-indigo-400 hover:text-indigo-300 flex items-center space-x-1 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                <span>Clear Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Timeline body display */}
        {loading ? (
          <TimelineLoader />
        ) : journals.length === 0 ? (
          <div className="bg-darkcard border border-darkborder rounded-2xl p-12 text-center shadow-sm max-w-lg mx-auto">
            <BookOpen className="h-10 w-10 text-indigo-500/30 mx-auto mb-4" />
            <h3 className="text-md font-bold text-gray-200">Every meaningful journey begins with a single reflection.</h3>
            <p className="text-xs text-gray-500 mt-2">
              Write your first journal to begin your story and map your daily emotional metrics.
            </p>
            <button
              onClick={() => navigate('/journal/new')}
              className="mt-6 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-6 rounded-xl text-xs transition-all duration-300 transform active:scale-95 btn-premium"
            >
              Compose Entry
            </button>
          </div>
        ) : (
          <div className="space-y-8 animate-fade-in">
            {Object.keys(groupedJournals).sort((a, b) => b.localeCompare(a)).map((year) => (
              <div key={year} className="space-y-6">
                
                {/* Year Header badge */}
                <div className="text-xl font-extrabold text-indigo-400 tracking-tight pl-2">
                  {year}
                </div>

                {Object.keys(groupedJournals[year]).sort((a, b) => {
                  // Sort months chronologically by index
                  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
                  return months.indexOf(b) - months.indexOf(a);
                }).map((month) => {
                  const monthKey = `${year}-${month}`;
                  const isCollapsed = collapsedMonths[monthKey] || false;
                  const monthEntries = groupedJournals[year][month];

                  return (
                    <div key={month} className="space-y-4">
                      
                      {/* Collapsible Month Toggle Header */}
                      <button
                        onClick={() => toggleMonth(monthKey)}
                        className="w-full flex items-center justify-between bg-darkcard/50 hover:bg-darkcard border border-darkborder rounded-xl px-4 py-2.5 transition-colors focus:outline-none"
                      >
                        <div className="flex items-center space-x-2">
                          {isCollapsed ? <ChevronRight className="h-4.5 w-4.5 text-gray-500" /> : <ChevronDown className="h-4.5 w-4.5 text-gray-500" />}
                          <span className="text-sm font-bold text-gray-300">{month}</span>
                          <span className="text-xs text-gray-500">({monthEntries.length} {monthEntries.length === 1 ? 'reflection' : 'reflections'})</span>
                        </div>
                      </button>

                      {/* Entries list inside month */}
                      {!isCollapsed && (
                        <div className="pl-6 border-l border-darkborder/50 ml-6 space-y-4 transition-all duration-300">
                          {monthEntries.map((entry) => {
                            const dateObj = new Date(entry.created_at);
                            const day = dateObj.getDate();
                            const weekday = dateObj.toLocaleDateString(undefined, { weekday: 'short' });

                            return (
                              <div 
                                key={entry.id}
                                className="relative bg-darkcard border border-darkborder hover:border-indigo-500/20 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col sm:flex-row justify-between items-start gap-4 group"
                              >
                                {/* Date node circle trace */}
                                <div className="absolute -left-[35px] top-6 w-4 h-4 bg-darkbg border-2 border-indigo-500/40 rounded-full flex items-center justify-center">
                                  <div className="h-1.5 w-1.5 bg-indigo-500 rounded-full"></div>
                                </div>

                                {/* Calendar Day Tag left */}
                                <div className="flex items-center space-x-3 sm:space-x-0 sm:flex-col sm:items-center w-14 shrink-0 text-center">
                                  <span className="text-xl font-black text-gray-200">{day}</span>
                                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">{weekday}</span>
                                </div>

                                {/* Entry Body info */}
                                <div className="flex-1 space-y-2">
                                  <div className="flex justify-between items-start">
                                    <h4 className="text-base font-bold text-gray-200 group-hover:text-indigo-400 transition-colors">
                                      {entry.title || 'Untitled Entry'}
                                    </h4>
                                    
                                    {/* Action button deck */}
                                    <div className="flex items-center space-x-2 opacity-10 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button
                                        onClick={() => navigate(`/journal/${entry.id}`)}
                                        className="text-gray-500 hover:text-indigo-400 p-1 rounded-lg hover:bg-darkbg transition-colors"
                                        title="Edit Entry"
                                      >
                                        <Edit3 className="h-4 w-4" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteEntry(entry.id)}
                                        className="text-gray-500 hover:text-red-400 p-1 rounded-lg hover:bg-darkbg transition-colors"
                                        title="Delete Entry"
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </button>
                                    </div>
                                  </div>

                                  <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                                    {entry.content.replace(/[#*`_]/g, '')}
                                  </p>

                                  {/* Footer stats tags */}
                                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                                    
                                    {/* Mapped Tags list */}
                                    <div className="flex flex-wrap gap-1">
                                      {entry.tags.map((t) => (
                                        <span 
                                          key={t.id}
                                          onClick={() => { setTagFilter(t.name); setSkip(0); }}
                                          className="bg-indigo-950/20 border border-indigo-500/10 text-indigo-400 text-[9px] px-2 py-0.5 rounded-full hover:bg-indigo-950 hover:text-indigo-300 transition-colors cursor-pointer"
                                        >
                                          #{t.name}
                                        </span>
                                      ))}
                                      {entry.tags.length === 0 && (
                                        <span className="text-[9px] text-gray-600 italic">No tags</span>
                                      )}
                                    </div>

                                    {/* Metrics icons indicators */}
                                    <div className="flex items-center space-x-3 text-[10px] text-gray-500">
                                      <span>Mood: <strong className="text-indigo-400 font-bold">{entry.mood}</strong></span>
                                      <span>Stress: <strong className="text-red-400 font-bold">{entry.stress_level}</strong></span>
                                      <span>Sleep: <strong className="text-yellow-500 font-bold">{Number(entry.sleep_hours)}h</strong></span>
                                    </div>

                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}

                    </div>
                  );
                })}

              </div>
            ))}

            {/* Pagination Controls */}
            <div className="flex justify-between items-center text-xs text-gray-500 pt-4 shrink-0">
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - limit))}
                className="flex items-center space-x-1.5 px-4 py-2 border border-darkborder bg-darkcard rounded-xl hover:border-indigo-500/30 disabled:opacity-30 disabled:hover:border-darkborder transition-all transform active:scale-95"
              >
                <ChevronRight className="h-4 w-4 rotate-180" />
                <span>Previous</span>
              </button>
              <span>Page {Math.floor(skip / limit) + 1}</span>
              <button
                disabled={!hasMore}
                onClick={() => setSkip(skip + limit)}
                className="flex items-center space-x-1.5 px-4 py-2 border border-darkborder bg-darkcard rounded-xl hover:border-indigo-500/30 disabled:opacity-30 disabled:hover:border-darkborder transition-all transform active:scale-95"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};
