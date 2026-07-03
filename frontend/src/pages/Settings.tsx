import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, api } from '../contexts/AuthContext';
import { 
  Brain, 
  LogOut, 
  Settings as SettingsIcon, 
  Save, 
  Download, 
  Bell, 
  Globe, 
  Palette, 
  ShieldAlert,
  Loader2,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';


export const Settings: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Settings states
  const [reminderEnabled, setReminderEnabled] = useState<boolean>(false);
  const [reminderTime, setReminderTime] = useState<string>('21:00');
  const [timezone, setTimezone] = useState<string>('UTC');
  const [theme, setTheme] = useState<string>('dark');

  // Page loading & action status
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Helper to show toasts
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
  };

  // Automatically fade out toast notifications
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  // Fetch preferences on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await api.get('/api/v1/settings');
        setReminderEnabled(res.data.reminder_enabled);
        setReminderTime(res.data.reminder_time);
        setTimezone(res.data.timezone);
        setTheme(res.data.theme);
      } catch (err) {
        console.error('Failed to load user settings:', err);
        showToast('Failed to load preferences.', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  // Update root element classes in real time when local theme changes
  useEffect(() => {
    document.body.classList.remove('theme-light', 'theme-glass');
    if (theme === 'light') {
      document.body.classList.add('theme-light');
    } else if (theme === 'glass') {
      document.body.classList.add('theme-glass');
    }
  }, [theme]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await api.put('/api/v1/settings', {
        reminder_enabled: reminderEnabled,
        reminder_time: reminderTime,
        timezone,
        theme
      });
      showToast('Settings saved successfully!', 'success');
      // Sync theme just in case
      setTheme(res.data.theme);
    } catch (err: any) {
      console.error('Failed to save settings:', err);
      const detail = err.response?.data?.detail;
      showToast(typeof detail === 'string' ? detail : 'Failed to save settings changes.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Download export blobs from streaming endpoints
  const handleExportHistory = async (format: 'md' | 'pdf') => {
    setExporting(true);
    showToast(`Compiling and starting download of your history as ${format.toUpperCase()}...`, 'info');
    try {
      const response = await api.get(`/api/v1/export/journals/all?format=${format}`, {
        responseType: 'blob'
      });
      const mime = format === 'md' ? 'text/markdown' : 'application/pdf';
      const blob = new Blob([response.data], { type: mime });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mindspace_history_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      showToast('Export downloaded successfully!', 'success');
    } catch (err: any) {
      console.error('Failed to export history:', err);
      showToast('Failed to compile export file.', 'error');
    } finally {
      setExporting(false);
    }
  };

  const handleLogoutClick = () => {
    logout();
    navigate('/login');
  };

  const timezoneOptions = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'America/Chicago', 
    'Europe/London', 'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney'
  ];

  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Top Navbar Header */}
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

        {/* Center Nav Link links */}
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
            className="text-xs text-gray-400 hover:text-gray-200 px-4 py-1.5 rounded-full transition-colors font-medium"
          >
            Analytics
          </Link>
          <Link 
            to="/settings" 
            className="bg-indigo-950/40 text-indigo-300 border border-indigo-500/20 text-xs px-4 py-1.5 rounded-full transition-colors font-semibold"
          >
            Settings
          </Link>
        </nav>

        {/* Right tools block */}
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

      {/* Main settings settings panels content */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-6 md:p-8 space-y-8 min-w-0">
        
        {/* Settings view Title banner */}
        <div className="border-b border-darkborder/30 pb-6">
          <h2 className="text-2xl font-black text-gray-100 flex items-center space-x-2">
            <SettingsIcon className="h-6 w-6 text-indigo-400 shrink-0" />
            <span>UserSettings & Preferences</span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Configure reminder triggers, download your journal history, or customize themes.
          </p>
        </div>

        {loading ? (
          <div className="h-96 flex items-center justify-center space-x-2">
            <Loader2 className="h-6 w-6 text-indigo-400 animate-spin" />
            <span className="text-xs text-gray-500 font-semibold">Loading preferences...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            
            {/* Left settings configuration Form */}
            <form onSubmit={handleSaveSettings} className="md:col-span-2 space-y-6">
              
              {/* Reminder Settings Card */}
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center space-x-2 border-b border-darkborder/40 pb-3">
                  <Bell className="h-4 w-4 text-indigo-400" />
                  <span>Journal Reminders</span>
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-semibold text-gray-300">Daily Writing Reminder</label>
                      <p className="text-[10px] text-gray-500">Enable daily notifications to maintain writing streaks.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer select-none">
                      <input 
                        type="checkbox" 
                        checked={reminderEnabled}
                        onChange={(e) => setReminderEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-darkborder/60 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-gray-400 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600 peer-checked:after:bg-gray-100"></div>
                    </label>
                  </div>

                  {reminderEnabled && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 animate-fade-in">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Reminder Time</label>
                        <input
                          type="text"
                          value={reminderTime}
                          onChange={(e) => setReminderTime(e.target.value)}
                          placeholder="e.g. 21:00"
                          className="w-full bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none font-bold placeholder-gray-700"
                        />
                        <p className="text-[9px] text-gray-500">Enter time in 24-hour HH:MM format.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Timezone & Regional Card */}
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center space-x-2 border-b border-darkborder/40 pb-3">
                  <Globe className="h-4 w-4 text-indigo-400" />
                  <span>Regional & Timezones</span>
                </h3>

                <div className="space-y-1.5 max-w-md">
                  <label className="text-xs font-semibold text-gray-300 block">Active Timezone</label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full bg-darkbg border border-darkborder focus:border-indigo-500/40 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none font-bold"
                  >
                    {timezoneOptions.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <p className="text-[10px] text-gray-500 mt-1">Configures timestamp offsets on journal dates aggregation.</p>
                </div>
              </div>

              {/* Themes Selector Card */}
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center space-x-2 border-b border-darkborder/40 pb-3">
                  <Palette className="h-4 w-4 text-indigo-400" />
                  <span>Visual Themes</span>
                </h3>

                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'dark', label: 'Slate Dark', desc: 'MindSpace baseline theme' },
                    { id: 'light', label: 'Alabaster Light', desc: 'Sleek white canvas theme' },
                    { id: 'glass', label: 'Aurora Glass', desc: 'Translucent neon backdrops' }
                  ].map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTheme(t.id)}
                      className={`p-4 border rounded-xl text-left space-y-1 focus:outline-none transition-all duration-300 ${
                        theme === t.id 
                          ? 'bg-indigo-950/30 border-indigo-500/60 shadow-md ring-1 ring-indigo-500/20' 
                          : 'bg-darkbg/40 border-darkborder hover:border-indigo-500/10'
                      }`}
                    >
                      <h4 className="text-xs font-bold text-gray-200">{t.label}</h4>
                      <p className="text-[9px] text-gray-500 leading-normal font-light">{t.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Form Action Controls buttons */}
              <div className="text-right">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-gray-100 font-bold py-2.5 px-6 rounded-xl text-xs transition-colors flex items-center space-x-2 ml-auto btn-premium"
                >
                  {saving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5" />
                  )}
                  <span>{saving ? 'Saving changes...' : 'Save Configuration'}</span>
                </button>
              </div>

            </form>

            {/* Right Export Center panel card */}
            <div className="space-y-6">
              
              <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 shadow-sm">
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center space-x-2 border-b border-darkborder/40 pb-3">
                  <Download className="h-4 w-4 text-indigo-400" />
                  <span>Export Center</span>
                </h3>
                
                <p className="text-xs text-gray-400 leading-relaxed font-light">
                  Export your compiled entries and metrics backups directly to local markdown or print-ready PDF files.
                </p>

                <div className="space-y-2 pt-2">
                  <button
                    onClick={() => handleExportHistory('md')}
                    disabled={exporting}
                    className="w-full bg-darkbg hover:bg-darkborder/30 border border-darkborder/60 hover:border-indigo-500/20 text-gray-300 font-bold py-2.5 px-4 rounded-xl text-xs flex items-center justify-between transition-all duration-300 hover:text-indigo-400 focus:outline-none"
                  >
                    <span>Export History as Markdown</span>
                    <Download className="h-3.5 w-3.5 text-gray-500" />
                  </button>

                  <button
                    onClick={() => handleExportHistory('pdf')}
                    disabled={exporting}
                    className="w-full bg-darkbg hover:bg-darkborder/30 border border-darkborder/60 hover:border-indigo-500/20 text-gray-300 font-bold py-2.5 px-4 rounded-xl text-xs flex items-center justify-between transition-all duration-300 hover:text-indigo-400 focus:outline-none"
                  >
                    <span>Export History as PDF</span>
                    <Download className="h-3.5 w-3.5 text-gray-500" />
                  </button>
                </div>

                <div className="border-t border-darkborder/30 pt-3">
                  <div className="flex items-start space-x-2 text-[10px] text-gray-500 leading-normal">
                    <ShieldAlert className="h-4 w-4 text-gray-500 shrink-0" />
                    <span>Your private journal drafts are exported locally and decrypted before save. Keep them safe.</span>
                  </div>
                </div>
              </div>

            </div>

          </div>
        )}

      </main>

      {/* Floating success/warning toast notifications popups */}
      {toast && (
        <div className={`fixed bottom-6 right-6 p-4 rounded-xl shadow-lg border text-xs leading-relaxed z-50 animate-fade-in flex items-center space-x-2.5 max-w-sm backdrop-blur-md ${
          toast.type === 'success' ? 'bg-emerald-950/90 border-emerald-500/30 text-emerald-300' :
          toast.type === 'error' ? 'bg-red-950/90 border-red-500/30 text-red-300' :
          'bg-indigo-950/90 border-indigo-500/30 text-indigo-300'
        }`}>
          {toast.type === 'success' && <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />}
          {toast.type === 'error' && <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />}
          {toast.type === 'info' && <Loader2 className="h-4 w-4 text-indigo-400 animate-spin shrink-0" />}
          <span>{toast.message}</span>
        </div>
      )}

    </div>
  );
};
