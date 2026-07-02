import React from 'react';

export const DashboardLoader: React.FC = () => {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Greeting Banner skeleton */}
      <div className="bg-darkcard border border-darkborder rounded-2xl p-8 h-48 flex flex-col justify-center space-y-4">
        <div className="h-6 bg-darkborder rounded w-1/3"></div>
        <div className="h-4 bg-darkborder rounded w-1/2"></div>
        <div className="h-10 bg-darkborder rounded w-32 mt-2"></div>
      </div>

      {/* Primary Grid Skeletons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recents list */}
        <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4">
          <div className="h-4 bg-darkborder rounded w-24 mb-4"></div>
          {[1, 2].map((n) => (
            <div key={n} className="h-16 bg-darkbg border border-darkborder/50 rounded-xl"></div>
          ))}
        </div>

        {/* Analytics skeletons lower */}
        <div className="bg-darkcard border border-darkborder rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div className="h-4 bg-darkborder rounded w-24"></div>
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-16 bg-darkbg border border-darkborder/50 rounded-xl flex items-center justify-center">
                <div className="h-5 bg-darkborder rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const TimelineLoader: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Search area skeleton */}
      <div className="h-12 bg-darkcard border border-darkborder rounded-xl w-full"></div>

      {/* Collapsible Month listings skeletons */}
      {[1, 2].map((m) => (
        <div key={m} className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-5 bg-darkborder rounded w-24"></div>
            <div className="h-4 bg-darkborder rounded w-12"></div>
          </div>
          <div className="space-y-4 pl-6 border-l border-darkborder/40">
            {[1, 2].map((card) => (
              <div key={card} className="bg-darkcard border border-darkborder rounded-2xl p-6 h-36 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="h-4 bg-darkborder rounded w-1/4"></div>
                  <div className="h-4 bg-darkborder rounded w-3/4"></div>
                </div>
                <div className="h-3 bg-darkborder rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
