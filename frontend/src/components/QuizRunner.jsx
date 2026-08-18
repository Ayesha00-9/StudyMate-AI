// One component used for BOTH "Generate Quiz" and "Exam Mode".
// The only difference is the label and the default number of questions,
// so there is no reason to write the same screen twice.
//
// Flow:  Start -> questions appear -> student answers -> Submit -> score + explanations
//
// The correct answers are never sent to the browser until after Submit,
// so they cannot be seen during the quiz or exam.

import { CheckCircle2, RotateCcw, XCircle } from "lucide-react";
import { useState } from "react";

import { createQuiz, readError, submitQuiz } from "../services/api.js";

export default function QuizRunner({ subjectId, kind = "quiz", practiceWeakTopics = false }) {
  const isExam = kind === "exam";

  const [count, setCount] = useState(isExam ? 10 : 5);
  const [quizId, setQuizId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [sources, setSources] = useState([]);
  const [answers, setAnswers] = useState([]);   // one chosen option index per question
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleStart() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await createQuiz(subjectId, count, kind, practiceWeakTopics);
      setQuizId(response.data.quiz_id);
      setQuestions(response.data.questions);
      setSources(response.data.sources);
      setAnswers(new Array(response.data.questions.length).fill(-1));
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  function chooseOption(questionIndex, optionIndex) {
    const updated = [...answers];
    updated[questionIndex] = optionIndex;
    setAnswers(updated);
  }

  async function handleSubmit() {
    if (answers.includes(-1)) {
      setError("Please answer every question before submitting.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await submitQuiz(quizId, answers);
      setResult(response.data);
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  function handleRestart() {
    setQuizId(null);
    setQuestions([]);
    setAnswers([]);
    setResult(null);
    setError("");
  }

  // ---------- Start screen ----------
  if (!quizId) {
    return (
      <div className="glass study-panel">
        <h3>{isExam ? "Exam Mode" : "Generate Quiz"}</h3>
        <p className="muted">
          {isExam
            ? "A longer test made from your uploaded material. No answers are shown until you submit."
            : "Multiple-choice questions made from your uploaded study material."}
          {practiceWeakTopics && " Questions will focus on the topics you got wrong before."}
        </p>

        {error && <div className="alert">{error}</div>}

        <div className="field" style={{ maxWidth: 220 }}>
          <label>Number of questions</label>
          <select
            className="input"
            value={count}
            onChange={(event) => setCount(Number(event.target.value))}
          >
            <option value={5}>5 questions</option>
            <option value={10}>10 questions</option>
          </select>
        </div>

        <button className="btn btn-primary" onClick={handleStart} disabled={loading}>
          {loading ? "Reading your material..." : isExam ? "Start Exam" : "Generate Quiz"}
        </button>
      </div>
    );
  }

  // ---------- Result screen ----------
  if (result) {
    return (
      <div className="glass study-panel">
        <div className="score-box">
          <div className="score-value">
            {result.score}/{result.total}
          </div>
          <div className="score-label">Score: {result.percentage}%</div>
        </div>

        {result.weak_topics.length > 0 && (
          <div className="weak-box">
            <strong>Needs Practice:</strong>
            <ol>
              {result.weak_topics.map((topic) => (
                <li key={topic}>{topic}</li>
              ))}
            </ol>
          </div>
        )}

        <h4 style={{ margin: "22px 0 12px" }}>Review</h4>

        {result.results.map((item, index) => (
          <div
            className={`review-item ${item.is_correct ? "correct" : "wrong"}`}
            key={index}
          >
            <div className="review-head">
              {item.is_correct ? (
                <CheckCircle2 size={17} color="#4ade80" />
              ) : (
                <XCircle size={17} color="#f87171" />
              )}
              <span>
                {index + 1}. {item.question}
              </span>
            </div>

            {!item.is_correct && (
              <div className="review-body">
                <p>
                  Your answer:{" "}
                  <span className="wrong-text">
                    {item.your_index >= 0 ? item.options[item.your_index] : "not answered"}
                  </span>
                </p>
                <p>
                  Correct answer:{" "}
                  <span className="correct-text">{item.options[item.correct_index]}</span>
                </p>
                <p className="explanation">{item.explanation}</p>
              </div>
            )}
          </div>
        ))}

        <button className="btn btn-ghost" onClick={handleRestart} style={{ marginTop: 18 }}>
          <RotateCcw size={15} /> Try another {isExam ? "exam" : "quiz"}
        </button>
      </div>
    );
  }

  // ---------- Questions screen ----------
  return (
    <div className="glass study-panel">
      <div className="study-panel-head">
        <h3>{isExam ? "Exam in progress" : "Quiz"}</h3>
        <span className="badge">
          {answers.filter((answer) => answer !== -1).length} / {questions.length} answered
        </span>
      </div>

      {sources.length > 0 && (
        <p className="rag-note">Based on your uploaded study material: {sources.join(", ")}</p>
      )}

      {error && <div className="alert">{error}</div>}

      {questions.map((question, questionIndex) => (
        <div className="question-card" key={questionIndex}>
          <div className="question-text">
            {questionIndex + 1}. {question.question}
          </div>
          {question.options.map((option, optionIndex) => (
            <label
              className={`option ${answers[questionIndex] === optionIndex ? "selected" : ""}`}
              key={optionIndex}
            >
              <input
                type="radio"
                name={`question-${questionIndex}`}
                checked={answers[questionIndex] === optionIndex}
                onChange={() => chooseOption(questionIndex, optionIndex)}
              />
              {option}
            </label>
          ))}
        </div>
      ))}

      <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
        {loading ? "Checking..." : "Submit Answers"}
      </button>
    </div>
  );
}
