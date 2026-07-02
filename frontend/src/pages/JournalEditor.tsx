import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth, api } from '../contexts/AuthContext';
import { Brain, LogOut, ArrowLeft, Trash2, Sparkles, X, Plus, Check, ShieldAlert } from 'lucide-react';

interface TagResponse {
  id: number;
  name: string;
}

interface AIReflection {
  id: number;
  journal_id: number;
  summary: string;
  detected_patterns: string[];
  reflection_question: string;
  generated_at: string;
  model_used: string;
  is_outdated?: boolean;
}

export const JournalEditor: React.FC = () => {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  // Model state variables
  const [entryId, setEntryId] = useState<number | null>(id ? parseInt(id) : null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [mood, setMood] = useState(3);
  const [stress, setStress] = useState(3);
  const [energy, setEnergy] = useState(3);
  const [sleep, setSleep] = useState(7.0);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  // AI Reflection states
  const [reflection, setReflection] = useState<AIReflection | null>(null);
  const [generating, setGenerating] = useState(false);
  const [aiError, setAiError] = useState('');

  // UI state variables
  const [savingStatus, setSavingStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [loading, setLoading] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);

  // Initial load locks
  const isFirstRender = useRef(true);
  const autosaveTimer = useRef<NodeJS.Timeout | null>(null);

  // Compute word and character count
  useEffect(() => {
    setCharCount(content.length);
    const words = content.trim().split(/\s+/).filter(w => w.length > 0);
    setWordCount(words.length);
  }, [content]);

  // Load existing entry & its cached AI reflection
  useEffect(() => {
    if (id) {
      setLoading(true);
      api.get(`/api/v1/journals/${id}`)
        .then((res) => {
          const entry = res.data;
          setEntryId(entry.id);
          setTitle(entry.title);
          setContent(entry.content);
          setMood(entry.mood);
          setStress(entry.stress_level);
          setEnergy(entry.energy_level);
          setSleep(Number(entry.sleep_hours));
          setTags(entry.tags.map((t: TagResponse) => t.name));
          setSavingStatus('saved');
          
          // Eager fetch existing reflection for this entry
          return api.get(`/api/v1/journals/${entry.id}/reflection`);
        })
        .then((reflectionRes) => {
          setReflection(reflectionRes.data);
        })
        .catch((err) => {
          // If reflection query returns 404, it means it's not generated yet, which is expected!
          if (err.response?.status === 404) {
            setReflection(null);
          } else {
            console.error("Failed to load journal details or reflection:", err);
          }
        })
        .finally(() => {
          setLoading(false);
          setTimeout(() => {
            isFirstRender.current = false;
          }, 100);
        });
    } else {
      setEntryId(null);
      setTitle('');
      setContent('');
      setMood(3);
      setStress(3);
      setEnergy(3);
      setSleep(7.0);
      setTags([]);
      setReflection(null);
      setAiError('');
      setSavingStatus('idle');
      isFirstRender.current = false;
    }
  }, [id, navigate]);

  // Debounced Autosave Trigger
  useEffect(() => {
    if (isFirstRender.current || loading) return;

    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    setSavingStatus('saving');

    autosaveTimer.current = setTimeout(() => {
      triggerSave();
    }, 2000);

    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    };
  }, [title, content, mood, stress, energy, sleep, tags]);

  // Save transaction handler
  const triggerSave = async () => {
    if (!title.trim() && !content.trim()) {
      setSavingStatus('idle');
      return null;
    }

    const payload = {
      title: title.trim() || 'Untitled Reflection',
      content: content,
      mood,
      stress_level: stress,
      energy_level: energy,
      sleep_hours: sleep,
      tags
    };

    try {
      if (entryId) {
        await api.put(`/api/v1/journals/${entryId}`, payload);
        setSavingStatus('saved');
        return entryId;
      } else {
        const res = await api.post('/api/v1/journals', payload);
        setEntryId(res.data.id);
        window.history.replaceState(null, '', `/journal/${res.data.id}`);
        setSavingStatus('saved');
        return res.data.id;
      }
    } catch (err) {
      console.error("Autosave write failed:", err);
      setSavingStatus('error');
      return null;
    }
  };

  // AI reflection generator helper
  const handleGenerateReflection = async () => {
    setGenerating(true);
    setAiError('');
    try {
      // First save changes so backend works with the latest drafts
      const activeId = await triggerSave();
      const targetId = entryId || activeId;

      if (!targetId) {
        setAiError("Please type a title or content before generating reflections.");
        setGenerating(false);
        return;
      }

      const res = await api.post(`/api/v1/journals/${targetId}/generate-reflection`);
      setReflection(res.data);
    } catch (err: any) {
      console.error("AI Reflection Generation failed:", err);
      const detail = err.response?.data?.detail || "AI reflection service currently unavailable. Please try again.";
      setAiError(detail);
    } finally {
      setGenerating(false);
    }
  };

  // Tag helper controls
  const handleTagAdd = () => {
    const cleaned = tagInput.trim().toLowerCase().replace(/[^a-zA-Z0-9-]/g, '');
    if (cleaned && !tags.includes(cleaned)) {
      setTags([...tags, cleaned]);
      setTagInput('');
    }
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleTagAdd();
    }
  };

  const handleTagRemove = (indexToRemove: number) => {
    setTags(tags.filter((_, i) => i !== indexToRemove));
  };

  const handleDeleteEntry = async () => {
    if (!entryId) return;
    if (!window.confirm("Are you sure you want to delete this reflection? (It can be recovered later).")) return;
    try {
      await api.delete(`/api/v1/journals/${entryId}`);
      navigate('/timeline');
    } catch (err) {
      console.error("Delete failed:", err);
    }
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
          <Link to="/timeline" className="text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors pb-1.5 pt-1">
            Timeline
          </Link>
          <span className="text-sm font-semibold text-indigo-400 border-b-2 border-indigo-500 pb-1.5 pt-1">
            Editor
          </span>
        </div>

        <button
          onClick={logout}
          className="flex items-center space-x-1.5 px-3 py-1.5 border border-darkborder hover:border-red-500/20 text-xs font-semibold rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-950/10 transition-all duration-300 transform active:scale-95"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </nav>

      {/* Main editor page container */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8 flex flex-col space-y-6 min-h-0 overflow-y-auto">
        
        {/* Editor controls bar */}
        <div className="flex items-center justify-between border-b border-darkborder pb-4 shrink-0">
          <button
            onClick={() => navigate('/timeline')}
            className="text-xs text-gray-400 hover:text-gray-200 transition-colors flex items-center space-x-1"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Close Editor</span>
          </button>
          
          {/* Status Indicator Bar */}
          <div className="flex items-center space-x-4">
            {savingStatus === 'saving' && (
              <span className="text-xs text-yellow-500/80 flex items-center space-x-1">
                <span className="h-1.5 w-1.5 bg-yellow-500 rounded-full animate-ping"></span>
                <span>Saving changes...</span>
              </span>
            )}
            {savingStatus === 'saved' && (
              <span className="text-xs text-green-500/80 flex items-center space-x-1">
                <Check className="h-3.5 w-3.5" />
                <span>Saved just now</span>
              </span>
            )}
            {savingStatus === 'error' && (
              <span className="text-xs text-red-400">Offline: Saving failed</span>
            )}
            {savingStatus === 'idle' && (
              <span className="text-xs text-gray-600">Draft static</span>
            )}

            {entryId && (
              <>
                <div className="h-4 w-px bg-darkborder"></div>
                <button
                  onClick={handleDeleteEntry}
                  className="text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-950/10 transition-colors"
                  title="Delete reflection"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center min-h-[300px]">
            <div className="text-center space-y-2">
              <Brain className="h-8 w-8 text-indigo-500 animate-spin mx-auto" />
              <p className="text-xs text-gray-500">Loading reflection canvas...</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col space-y-8 animate-fade-in pb-12">
            {/* Writing canvas */}
            <div className="flex flex-col space-y-4">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Title your reflection..."
                aria-label="Journal entry title"
                className="bg-transparent border-none text-3xl md:text-4xl font-extrabold text-gray-100 placeholder-gray-700 focus:outline-none focus:ring-0 focus:border-transparent w-full"
              />

              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your story here... Supports Markdown syntax."
                aria-label="Journal entry content text"
                className="bg-transparent border-none resize-none focus:outline-none focus:ring-0 focus:border-transparent text-gray-300 placeholder-gray-800 text-md leading-relaxed font-serif min-h-[300px] w-full"
              />
              
              <div className="flex justify-between items-center text-[10px] text-gray-600 border-t border-darkborder/50 pt-2 shrink-0">
                <span>Markdown support enabled</span>
                <span>{wordCount} words • {charCount} chars</span>
              </div>
            </div>

            {/* Structured Metric sliders card placed below the entry */}
            <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-6 shadow-sm">
              <div className="flex items-center space-x-1.5 text-xs text-gray-400 font-semibold border-b border-darkborder/60 pb-3">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                <span>Today's Reflection Metrics</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
                
                {/* Mood Selector slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gray-400">Mood</span>
                    <span className="text-indigo-400 font-bold">{mood} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={mood}
                    onChange={(e) => setMood(parseInt(e.target.value))}
                    className="w-full h-1 bg-darkborder rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <div className="flex justify-between text-[9px] text-gray-600">
                    <span>Exhausted</span>
                    <span>Vibrant</span>
                  </div>
                </div>

                {/* Stress Selector slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gray-400">Stress</span>
                    <span className="text-red-400 font-bold">{stress} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={stress}
                    onChange={(e) => setStress(parseInt(e.target.value))}
                    className="w-full h-1 bg-darkborder rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <div className="flex justify-between text-[9px] text-gray-600">
                    <span>Calm</span>
                    <span>Anxious</span>
                  </div>
                </div>

                {/* Energy Selector slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gray-400">Energy</span>
                    <span className="text-green-400 font-bold">{energy} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={energy}
                    onChange={(e) => setEnergy(parseInt(e.target.value))}
                    className="w-full h-1 bg-darkborder rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <div className="flex justify-between text-[9px] text-gray-600">
                    <span>Low energy</span>
                    <span>Vibrant</span>
                  </div>
                </div>

                {/* Sleep Hours selector input */}
                <div className="space-y-2 flex flex-col justify-center">
                  <label className="text-xs font-semibold text-gray-400 block">Sleep Duration</label>
                  <div className="flex items-center space-x-2 mt-1">
                    <input
                      type="number"
                      min="0"
                      max="24"
                      step="0.5"
                      value={sleep}
                      onChange={(e) => setSleep(Math.max(0, parseFloat(e.target.value) || 0))}
                      className="w-20 bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-lg px-2.5 py-1 text-sm text-gray-200 focus:outline-none font-bold"
                    />
                    <span className="text-xs text-gray-500">hours sleep</span>
                  </div>
                </div>

              </div>
            </div>

            {/* Custom tags manager board below sliders */}
            <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
              <label className="text-xs font-semibold text-gray-400 block">Categorization Tags</label>
              
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="bg-indigo-950/40 border border-indigo-500/20 text-indigo-300 text-xs px-3 py-1 rounded-full flex items-center space-x-1.5"
                  >
                    <span>#{tag}</span>
                    <button
                      onClick={() => handleTagRemove(idx)}
                      className="hover:text-red-400 transition-colors focus:outline-none"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                {tags.length === 0 && (
                  <span className="text-xs text-gray-600 italic">No tags added yet. Categorize your entries below.</span>
                )}
              </div>

              <div className="flex items-center space-x-2 max-w-sm pt-2">
                <input
                  type="text"
                  placeholder="New tag... (Press enter)"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagInputKeyDown}
                  className="flex-1 bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-lg px-3 py-1.5 text-xs text-gray-200 focus:outline-none placeholder-gray-600"
                />
                <button
                  onClick={handleTagAdd}
                  className="bg-indigo-950/40 border border-indigo-500/20 hover:bg-indigo-900/40 text-indigo-300 p-2 rounded-lg transition-colors btn-premium"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* AI Reflection Insights Card */}
            {entryId && (
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-darkborder/60 pb-3">
                  <div className="flex items-center space-x-1.5 text-xs text-indigo-400 font-bold uppercase tracking-wider">
                    <Sparkles className="h-4.5 w-4.5 text-indigo-400 animate-pulse shrink-0" />
                    <span>MindSpace AI Reflection</span>
                  </div>
                  {reflection && (
                    <span className="text-[10px] text-gray-500 font-medium">
                      Model: {reflection.model_used}
                    </span>
                  )}
                </div>

                {generating ? (
                  <div className="space-y-3 py-4 animate-pulse">
                    <div className="h-4 bg-darkborder rounded w-1/3"></div>
                    <div className="h-4 bg-darkborder rounded w-3/4"></div>
                    <div className="h-4 bg-darkborder rounded w-1/2"></div>
                  </div>
                ) : aiError ? (
                  <div className="p-4 border border-red-500/20 bg-red-950/10 rounded-xl text-xs text-red-400 space-y-2">
                    <p className="font-semibold">Reflection generation failed</p>
                    <p>{aiError}</p>
                    <button
                      onClick={handleGenerateReflection}
                      className="text-indigo-400 hover:text-indigo-300 font-semibold underline block"
                    >
                      Retry generation
                    </button>
                  </div>
                ) : reflection ? (
                  <div className="space-y-4 animate-fade-in">
                    
                    {/* Crisis safefilter indicator support page */}
                    {reflection.model_used === 'safety_filter' ? (
                      <div className="p-4 border border-red-500/30 bg-red-950/15 rounded-xl space-y-3">
                        <h4 className="text-sm font-bold text-red-400 flex items-center space-x-1.5">
                          <ShieldAlert className="h-5 w-5 text-red-400 shrink-0" />
                          <span>Support Helpline Resource</span>
                        </h4>
                        <p className="text-xs text-gray-300 leading-relaxed">
                          {reflection.summary}
                        </p>
                        <div className="p-3 bg-red-950/30 border border-red-500/10 rounded-lg text-xs font-serif italic text-red-300 leading-relaxed">
                          {reflection.reflection_question}
                        </div>
                      </div>
                    ) : (
                      <>
                        {reflection.is_outdated && (
                          <div className="p-3 border border-yellow-500/20 bg-yellow-950/10 rounded-xl text-xs text-yellow-500/90 leading-relaxed flex items-center space-x-2">
                            <ShieldAlert className="h-4 w-4 text-yellow-500 shrink-0" />
                            <span>AI service is temporarily busy. A fallback cached reflection has been displayed.</span>
                          </div>
                        )}
                        <p className="text-sm text-gray-300 leading-relaxed font-sans">
                          {reflection.summary}
                        </p>

                        <div className="space-y-2">
                          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Detected Patterns & Emotions</span>
                          <div className="flex flex-wrap gap-1">
                            {reflection.detected_patterns.map((pattern: string, idx: number) => (
                              <span
                                key={idx}
                                className="bg-indigo-950/40 border border-indigo-500/20 text-indigo-300 text-[10px] px-2.5 py-0.5 rounded-full"
                              >
                                {pattern}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="bg-indigo-900/10 border border-indigo-500/10 rounded-xl p-4 space-y-1.5">
                          <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Reflective Prompt</span>
                          <p className="text-xs text-indigo-200 font-serif italic leading-relaxed">
                            {reflection.reflection_question}
                          </p>
                        </div>

                        <div className="text-right">
                          <button
                            onClick={handleGenerateReflection}
                            className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold underline focus:outline-none"
                          >
                            Re-analyze entry content
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <div className="py-6 text-center space-y-3 max-w-sm mx-auto">
                    <p className="text-xs text-gray-400 leading-relaxed">
                      Analyze emotional highlights, trace habits, and receive open-ended reflection prompts.
                    </p>
                    <button
                      onClick={handleGenerateReflection}
                      className="bg-indigo-950/40 border border-indigo-500/20 hover:bg-indigo-900/40 text-indigo-300 font-semibold py-2 px-5 rounded-xl text-xs transition-colors btn-premium"
                    >
                      Generate Reflection Insights
                    </button>
                  </div>
                )}
              </div>
            )}

          </div>
        )}
      </main>
    </div>
  );
};
