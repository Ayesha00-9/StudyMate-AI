// All the routes of the application.
// Pages that need a logged-in user are wrapped in <ProtectedRoute>.

import { Navigate, Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Chat from "./pages/Chat.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Landing from "./pages/Landing.jsx";
import Register from "./pages/Register.jsx";
import Study from "./pages/Study.jsx";
import SubjectDetail from "./pages/SubjectDetail.jsx";
import Subjects from "./pages/Subjects.jsx";
import { isLoggedIn } from "./services/auth.js";

// Small helper so a logged-in user does not see the login page again.
function PublicOnly({ children }) {
  return isLoggedIn() ? <Navigate to="/dashboard" replace /> : children;
}

// Pages that share the top navigation bar.
function WithNavbar({ children }) {
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicOnly>
            <Landing />
          </PublicOnly>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnly>
            <Register />
          </PublicOnly>
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <WithNavbar>
              <Dashboard />
            </WithNavbar>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subjects"
        element={
          <ProtectedRoute>
            <WithNavbar>
              <Subjects />
            </WithNavbar>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subjects/:subjectId"
        element={
          <ProtectedRoute>
            <WithNavbar>
              <SubjectDetail />
            </WithNavbar>
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <WithNavbar>
              <Chat />
            </WithNavbar>
          </ProtectedRoute>
        }
      />
      <Route
        path="/study"
        element={
          <ProtectedRoute>
            <WithNavbar>
              <Study />
            </WithNavbar>
          </ProtectedRoute>
        }
      />

      {/* Anything else goes back to the start. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
