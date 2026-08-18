// Study Tools page: Quiz, Exam Mode, Flashcards and Summary in one place.
// Everything on this page works from the selected subject's uploaded material.

import { BookOpenCheck, FileText, GraduationCap, Layers, ListChecks } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useSearchParams } from "react-router-dom";

import FlashcardDeck from "../components/FlashcardDeck.jsx";
import QuizRunner from "../components/QuizRunner.jsx";
import { getSubjects, getSummary, readError } from "../services/api.js";

const TABS = [
  { key: "quiz", label: "Generate Quiz", icon: <ListChecks size={16} /> },
  { key: "exam", label: "Exam Mode", icon: <GraduationCap size={16} /> },
  { key: "flashcards", label: "Flashcards", icon: <Layers size={16} /> },
  { key: "summary", label: "Summary", icon: <BookOpenCheck size={16} /> },
];

export default function Study() {
  const [searchParams] = useSearchParams();

  const [subjects, setSubjects] = useState([]);
  const [subjectId, setSubjectId] = useState(searchParams.get("subject") || "");
  const [tab, setTab] = useState(searchParams.get("tab") || "quiz");

  // "Practice Weak Topics" from the dashboard opens this page with weak=1.
  // It is state (not read straight from the URL) so it can be switched off
  // again when the student picks a different subject or tab.
  const [practiceWeakTopics, setPracticeWeakTopics] = useState(
    searchParams.get("weak") === "1"
  );

  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSubjects() {
      try {
        const response = await getSubjects();
        setSubjects(response.data);
        // Pick the first subject automatically so the page is usable right away.
        if (!subjectId && response.data.length > 0) {
          setSubjectId(response.data[0].id);
        }
      } catch (err) {
        setError(readError(err));
      }
    }
    loadSubjects();
  }, []);

  return (
    <div className="container page fade-up">
      <div className="page-head">
        <h1>Study Tools</h1>
        <p>Quizzes, exams, flashcards and summaries made from your own notes.</p>
      </div>

      {error && <div className="alert">{error}</div>}

      {subjects.length === 0 ? (
        <div className="glass empty">
          <h3>No subjects yet</h3>
          <p>Create a subject and upload your notes first.</p>
        </div>
      ) : (
        <>
          <div className="study-controls">
            <div className="field" style={{ margin: 0, minWidth: 240 }}>
              <label>Subject</label>
              <select
                className="input"
                value={subjectId}
                onChange={(event) => {
                  setSubjectId(event.target.value);
                  setPracticeWeakTopics(false); // a new subject means a normal quiz
                }}
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name} ({subject.document_count} files)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="tab-row">
            {TABS.map((item) => (
              <button
                key={item.key}
                className={`tab ${tab === item.key ? "active" : ""}`}
                onClick={() => {
                  setTab(item.key);
                  setPracticeWeakTopics(false);
                }}
              >
                {item.icon} {item.label}
              </button>
            ))}
          </div>

          {practiceWeakTopics && tab === "quiz" && (
            <div className="alert alert-success">
              Practice mode: these questions focus on the topics you answered wrong before.
            </div>
          )}

          {/* key={...} restarts the panel when the subject or tab changes */}
          {tab === "quiz" && (
            <QuizRunner
              key={`quiz-${subjectId}`}
              subjectId={subjectId}
              kind="quiz"
              practiceWeakTopics={practiceWeakTopics}
            />
          )}
          {tab === "exam" && (
            <QuizRunner key={`exam-${subjectId}`} subjectId={subjectId} kind="exam" />
          )}
          {tab === "flashcards" && <FlashcardDeck key={`cards-${subjectId}`} subjectId={subjectId} />}
          {tab === "summary" && <SummaryPanel key={`sum-${subjectId}`} subjectId={subjectId} />}
        </>
      )}
    </div>
  );
}

// Small panel kept in this file because it is only a few lines.
function SummaryPanel({ subjectId }) {
  const [summary, setSummary] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setLoading(true);
    setError("");
    try {
      const response = await getSummary(subjectId);
      setSummary(response.data.summary);
      setSources(response.data.sources);
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass study-panel">
      <h3>Study Summary</h3>
      <p className="muted">
        Main Concepts, Important Definitions, Key Points and Exam-Focused Notes, taken
        from your uploaded material.
      </p>

      {error && <div className="alert">{error}</div>}

      <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
        {loading ? "Reading your material..." : "Generate Summary"}
      </button>

      {summary && (
        <>
          {sources.length > 0 && (
            <p className="rag-note" style={{ marginTop: 20 }}>
              <FileText size={12} /> Based on your uploaded study material:{" "}
              {sources.join(", ")}
            </p>
          )}
          <div className="summary-body">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>
        </>
      )}
    </div>
  );
}
