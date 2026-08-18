// Create a new account.

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import SocialLogin from "../components/SocialLogin.jsx";
import { readError, registerUser } from "../services/api.js";
import { saveSession } from "../services/auth.js";

export default function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRegister(event) {
    event.preventDefault();
    setError("");

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const response = await registerUser(name, email, password);
      saveSession(response.data.access_token, response.data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="glass auth-card fade-up">
        <div className="brand" style={{ marginBottom: 22 }}>
          <span className="brand-mark">
            <Sparkles size={19} />
          </span>
          StudyMate <span className="gradient-text">AI</span>
        </div>

        <h2>Create your account</h2>
        <p className="muted">Start learning with your own AI study companion.</p>

        {error && <div className="alert">{error}</div>}

        <form onSubmit={handleRegister}>
          <div className="field">
            <label>Full name</label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ayesha Amjad Ali"
              required
            />
          </div>

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
              placeholder="At least 6 characters"
              required
            />
          </div>

          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <SocialLogin />

        <p className="auth-footer">
          Already have an account? <Link to="/">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
