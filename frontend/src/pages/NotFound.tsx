import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, HelpCircle } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-md w-full bg-darkcard border border-darkborder rounded-2xl p-8 text-center space-y-6 shadow-xl">
        <div className="flex justify-center">
          <div className="bg-indigo-600/10 border border-indigo-500/20 p-4 rounded-full">
            <HelpCircle className="h-12 w-12 text-indigo-400 animate-pulse" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-4xl font-black text-gray-100">404</h1>
          <h2 className="text-lg font-bold text-gray-200 uppercase tracking-wider">Page Not Found</h2>
          <p className="text-xs text-gray-400 leading-relaxed font-light">
            The page you are looking for does not exist or has been moved. Let's return to safety.
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-gray-100 font-bold py-2.5 px-6 rounded-xl text-xs transition-colors btn-premium"
        >
          <Brain className="h-3.5 w-3.5" />
          <span>Go back to Dashboard</span>
        </Link>
      </div>
    </div>
  );
};
