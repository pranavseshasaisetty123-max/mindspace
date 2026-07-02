import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, loading } = useAuth();

  // Simple loading splash screen during JWT verification
  if (loading) {
    return (
      <div className="min-h-screen bg-darkbg flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  // Redirect to login if user isn't authenticated
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
