// Landing page + login form.

import { BrainCircuit, FileText, Loader2, MessagesSquare, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import SocialLogin from "../components/SocialLogin.jsx";
import { loginUser, readError } from "../services/api.js";
import { saveSession } from "../services/auth.js";

export default function Landing() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await loginUser(email, password);
      saveSession(response.data.access_token, response.data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="landing">
      <div className="container landing-grid">
        {/* ---- Left side: the brand ---- */}
        <div className="fade-up">
          <span className="badge">
            <Sparkles size={13} /> Powered by GPT-4o-mini + RAG
          </span>

          <h1 className="hero-title">
            Study Smarter.
            <br />
            Ask Better.
            <br />
            <span className="gradient-text">Learn Faster.</span>
          </h1>

          <p className="hero-sub">
            Your AI-powered study companion. Chat with an AI tutor, upload your own
            lecture notes and get answers straight from your study material.
          </p>

          <div className="feature-row">
            <div className="feature-pill">
              <MessagesSquare size={15} /> AI Chat
            </div>
            <div className="feature-pill">
              <FileText size={15} /> PDF, DOCX &amp; TXT
            </div>
            <div className="feature-pill">
              <BrainCircuit size={15} /> Answers from your notes
            </div>
          </div>

          <p className="hero-author">
            By <strong>Ayesha Amjad Ali</strong>
          </p>
        </div>

        {/* ---- Right side: login ---- */}
        <div className="glass auth-card fade-up">
          <h2>Welcome back</h2>
          <p className="muted">Sign in to continue studying.</p>

          {error && <div className="alert">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="field">
              <label>Email</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                required
              />
            </div>

            <div className="field">
              <label>Password</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <button className="btn btn-primary btn-block" disabled={loading}>
              {loading ? <Loader2 size={17} className="spin" /> : null}
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <SocialLogin />

          <p className="auth-footer">
            New here? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
