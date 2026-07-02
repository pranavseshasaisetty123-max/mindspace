import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { JournalEditor } from './pages/JournalEditor';
import { Timeline } from './pages/Timeline';
import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
          
          {/* Redirect any other route back to dashboard root */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
