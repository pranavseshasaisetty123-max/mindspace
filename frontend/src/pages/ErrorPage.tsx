import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface ErrorPageProps {
  error?: Error;
  resetErrorBoundary?: () => void;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({ error, resetErrorBoundary }) => {
  return (
    <div className="min-h-screen bg-darkbg text-gray-100 flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-md w-full bg-darkcard border border-darkborder rounded-2xl p-8 text-center space-y-6 shadow-xl">
        <div className="flex justify-center">
          <div className="bg-red-600/10 border border-red-500/20 p-4 rounded-full">
            <AlertOctagon className="h-12 w-12 text-red-400" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-xl font-black text-gray-100 uppercase tracking-wide">Something Went Wrong</h1>
          <p className="text-xs text-gray-400 leading-relaxed font-light">
            An unexpected client rendering error occurred. Please attempt to reset or reload the app context.
          </p>
          {error && (
            <div className="bg-darkbg border border-darkborder/50 text-left p-3 rounded-xl max-h-24 overflow-y-auto text-[10px] text-red-300 font-mono break-all leading-normal mt-2">
              {error.message || String(error)}
            </div>
          )}
        </div>

        {resetErrorBoundary ? (
          <button
            onClick={resetErrorBoundary}
            className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-gray-100 font-bold py-2.5 px-6 rounded-xl text-xs transition-colors btn-premium focus:outline-none"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset App Context</span>
          </button>
        ) : (
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-gray-100 font-bold py-2.5 px-6 rounded-xl text-xs transition-colors btn-premium focus:outline-none"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reload Page</span>
          </button>
        )}
      </div>
    </div>
  );
};
