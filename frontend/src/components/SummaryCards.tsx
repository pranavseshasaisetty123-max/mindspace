import React from 'react';
import { Flame, BookOpen, Smile, Clock } from 'lucide-react';

interface SummaryData {
  total_reflections: number;
  streak_days: number;
  average_mood: number;
  average_sleep: number;
}

interface SummaryCardsProps {
  summary: SummaryData;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in shrink-0">
      
      {/* Writing Streak Card */}
      <div className="bg-darkcard border border-darkborder rounded-2xl p-5 space-y-3 shadow-sm hover:border-indigo-500/10 transition-colors">
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-gray-400">Writing Streak</span>
          <div className="p-2 bg-indigo-950/30 rounded-xl">
            <Flame className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <h3 className="text-2xl font-black text-gray-100">{summary.streak_days}</h3>
          <p className="text-[10px] text-gray-500 mt-1 font-light">consecutive days</p>
        </div>
      </div>

      {/* Total Reflections Card */}
      <div className="bg-darkcard border border-darkborder rounded-2xl p-5 space-y-3 shadow-sm hover:border-indigo-500/10 transition-colors">
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-gray-400">Total Entries</span>
          <div className="p-2 bg-indigo-950/30 rounded-xl">
            <BookOpen className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <h3 className="text-2xl font-black text-gray-100">{summary.total_reflections}</h3>
          <p className="text-[10px] text-gray-500 mt-1 font-light">reflections logged</p>
        </div>
      </div>

      {/* Average Mood Card */}
      <div className="bg-darkcard border border-darkborder rounded-2xl p-5 space-y-3 shadow-sm hover:border-indigo-500/10 transition-colors">
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-gray-400">Average Mood</span>
          <div className="p-2 bg-indigo-950/30 rounded-xl">
            <Smile className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <h3 className="text-2xl font-black text-gray-100">{summary.average_mood} <span className="text-xs text-gray-500">/ 5</span></h3>
          <p className="text-[10px] text-gray-500 mt-1 font-light">emotional baseline</p>
        </div>
      </div>

      {/* Average Sleep Card */}
      <div className="bg-darkcard border border-darkborder rounded-2xl p-5 space-y-3 shadow-sm hover:border-indigo-500/10 transition-colors">
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-gray-400">Average Sleep</span>
          <div className="p-2 bg-indigo-950/30 rounded-xl">
            <Clock className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <h3 className="text-2xl font-black text-gray-100">{summary.average_sleep} <span className="text-xs text-gray-500">h</span></h3>
          <p className="text-[10px] text-gray-500 mt-1 font-light">hours sleep duration</p>
        </div>
      </div>

    </div>
  );
};
