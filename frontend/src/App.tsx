import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { JournalEditor } from './pages/JournalEditor';
import { Timeline } from './pages/Timeline';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { NotFound } from './pages/NotFound';
import { ProtectedRoute } from './components/ProtectedRoute';
import { ErrorBoundary } from './components/ErrorBoundary';
import { OfflineBanner } from './components/OfflineBanner';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <OfflineBanner />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected Timelines and Editor Dashboards */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/timeline" 
              element={
                <ProtectedRoute>
                  <Timeline />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/settings" 
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/journal/new" 
              element={
                <ProtectedRoute>
                  <JournalEditor />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/journal/:id" 
              element={
                <ProtectedRoute>
                  <JournalEditor />
                </ProtectedRoute>
              } 
            />
            
            {/* Fallback route to 404 page */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
