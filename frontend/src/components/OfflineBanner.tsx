import React, { useState, useEffect } from 'react';
import { WifiOff } from 'lucide-react';

export const OfflineBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="bg-amber-600 text-gray-100 text-center py-2 px-4 flex items-center justify-center space-x-2 text-xs font-bold w-full z-50 sticky top-0 shadow-md">
      <WifiOff className="h-4 w-4 shrink-0 text-white animate-pulse" />
      <span>You are currently offline. Check your connection to sync your journal reflections.</span>
    </div>
  );
};
