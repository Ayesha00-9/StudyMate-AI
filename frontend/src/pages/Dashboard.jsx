// Dashboard: statistics, subject cards and recent conversations.

import {
  BookOpen,
  FileText,
  MessagesSquare,
  Plus,
  Target,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  getConversations,
  getProgress,
  getStats,
  getSubjects,
  readError,
} from "../services/api.js";
import { getUser } from "../services/auth.js";

export default function Dashboard() {
  const navigate = useNavigate();
  const user = getUser();

  const [stats, setStats] = useState({
    total_subjects: 0,
    total_documents: 0,
    total_conversations: 0,
  });
  const [subjects, setSubjects] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState("");

  // Load everything once when the page opens.
  useEffect(() => {
    async function loadDashboard() {
      try {
        // Promise.allSettled instead of Promise.all: if one of the four calls
        // fails, the other three still fill the page instead of the dashboard
        // going completely blank.
        const [statsResult, subjectsResult, conversationsResult, progressResult] =
          await Promise.allSettled([
            getStats(),
            getSubjects(),
            getConversations(),
            getProgress(),
          ]);

        if (statsResult.status === "fulfilled") setStats(statsResult.value.data);
        if (subjectsResult.status === "fulfilled") setSubjects(subjectsResult.value.data);
        if (conversationsResult.status === "fulfilled") {
          setConversations(conversationsResult.value.data.slice(0, 5));
        }
        if (progressResult.status === "fulfilled") setProgress(progressResult.value.data);

        // Show a message only if something actually failed.
        const failed = [statsResult, subjectsResult, conversationsResult, progressResult]
          .find((result) => result.status === "rejected");
        if (failed) setError(readError(failed.reason));
      } catch (err) {
        setError(readError(err));
      }
    }
    loadDashboard();
  }, []);

  function formatDate(isoDate) {
    return new Date(isoDate).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
    });
  }

  const cards = [
    { label: "Subjects", value: stats.total_subjects, icon: <BookOpen size={21} /> },
    { label: "Documents", value: stats.total_documents, icon: <FileText size={21} /> },
    {
      label: "Conversations",
      value: stats.total_conversations,
      icon: <MessagesSquare size={21} />,
    },
  ];

  return (
    <div className="container page fade-up">
      <div className="page-head">
        <h1>
          Welcome back, <span className="gradient-text">{user?.name?.split(" ")[0]}</span>!
        </h1>
        <p>Here is what is happening in your study space.</p>
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="stats-grid">
        {cards.map((card) => (
          <div className="card-3d" key={card.label}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-value">{card.value}</div>
            <div className="stat-label">Total {card.label}</div>
          </div>
        ))}
      </div>

      {/* ---- Study progress (Features 9 and 10) ---- */}
      {progress && (
        <>
          <div className="section-head">
            <h2>Study Progress</h2>
          </div>

          <div className="grid-2">
            <div className="card-3d">
              <div className="stat-icon">
                <TrendingUp size={20} />
              </div>
              <div className="progress-rows">
                <div className="progress-row">
                  <span>Questions Asked</span>
                  <strong>{progress.questions_asked}</strong>
                </div>
                <div className="progress-row">
                  <span>Quizzes Completed</span>
                  <strong>{progress.quizzes_completed}</strong>
                </div>
                <div className="progress-row">
                  <span>Average Score</span>
                  <strong>{progress.average_score}%</strong>
                </div>
                <div className="progress-row">
                  <span>Uploaded Documents</span>
                  <strong>{progress.total_documents}</strong>
                </div>
              </div>
              {/* Simple bar showing the average quiz score */}
              <div className="progress-bar">
                <div style={{ width: `${progress.average_score}%` }} />
              </div>
            </div>

            <div className="card-3d">
              <div className="stat-icon">
                <Target size={20} />
              </div>
              <h3>Needs Practice</h3>
              {progress.weak_topics.length === 0 ? (
                <p style={{ color: "var(--text-dim)", fontSize: 14 }}>
                  No weak topics yet. Take a quiz to find out where to focus.
                </p>
              ) : (
                <ol className="weak-list">
                  {progress.weak_topics.map((topic) => (
                    <li key={topic}>{topic}</li>
                  ))}
                </ol>
              )}
              <Link
                to="/study?tab=quiz&weak=1"
                className="btn btn-primary btn-sm"
                style={{ marginTop: 16 }}
              >
                <Target size={14} /> Practice Weak Topics
              </Link>
            </div>
          </div>
        </>
      )}

      {/* ---- Subjects ---- */}
      <div className="section-head">
        <h2>Your Subjects</h2>
        <Link to="/subjects" className="btn btn-ghost btn-sm">
          <Plus size={15} /> Manage
        </Link>
      </div>

      {subjects.length === 0 ? (
        <div className="glass empty">
          <h3>No subjects yet</h3>
          <p>Create a subject and upload your notes to start using RAG.</p>
          <Link
            to="/subjects"
            className="btn btn-primary btn-sm"
            style={{ marginTop: 18 }}
          >
            <Plus size={15} /> Create Subject
          </Link>
        </div>
      ) : (
        <div className="grid-3">
          {subjects.map((subject) => (
            <div
              className="card-3d subject-card"
              key={subject.id}
              onClick={() => navigate(`/subjects/${subject.id}`)}
              style={{ cursor: "pointer" }}
            >
              <div className="stat-icon">
                <BookOpen size={20} />
              </div>
              <h3>{subject.name}</h3>
              <p>{subject.description || "No description"}</p>
              <div className="row">
                <span className="badge">
                  <FileText size={12} /> {subject.document_count} files
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ---- Recent chats ---- */}
      <div className="section-head">
        <h2>Recent Conversations</h2>
        <Link to="/chat" className="btn btn-ghost btn-sm">
          <MessagesSquare size={15} /> Open Chat
        </Link>
      </div>

      {conversations.length === 0 ? (
        <div className="glass empty">
          <h3>No conversations yet</h3>
          <p>Ask StudyMate AI your first question.</p>
        </div>
      ) : (
        conversations.map((conversation) => (
          <Link
            to={`/chat?conversation=${conversation.id}`}
            className="recent-item"
            key={conversation.id}
          >
            <MessagesSquare size={17} color="#8b5cf6" />
            <span className="title">{conversation.title}</span>
            <span className="time">{formatDate(conversation.updated_at)}</span>
          </Link>
        ))
      )}
    </div>
  );
}
