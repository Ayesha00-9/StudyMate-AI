// Blocks a page if there is no saved login token.

import { Navigate } from "react-router-dom";
import { isLoggedIn } from "../services/auth.js";

export default function ProtectedRoute({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/" replace />;
  }
  return children;
}
