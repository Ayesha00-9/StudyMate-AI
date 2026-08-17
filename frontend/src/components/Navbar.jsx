// Top navigation bar shown on every page after login.

import { BookOpen, LayoutDashboard, LogOut, MessagesSquare, Sparkles } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { getUser, logout } from "../services/auth.js";

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <NavLink to="/dashboard" className="brand">
          <span className="brand-mark">
            <Sparkles size={19} />
          </span>
          StudyMate <span className="gradient-text">AI</span>
        </NavLink>

        <div className="nav-links">
          <NavLink to="/dashboard" className="nav-link">
            <LayoutDashboard size={17} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/chat" className="nav-link">
            <MessagesSquare size={17} />
            <span>Chat</span>
          </NavLink>
          <NavLink to="/subjects" className="nav-link">
            <BookOpen size={17} />
            <span>Subjects</span>
          </NavLink>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
            <LogOut size={15} />
            {user ? user.name.split(" ")[0] : "Logout"}
          </button>
        </div>
      </div>
    </nav>
  );
}
