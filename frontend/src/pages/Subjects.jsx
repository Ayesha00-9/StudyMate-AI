// Create, view and delete subjects.

import { BookOpen, FileText, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Modal from "../components/Modal.jsx";
import {
  createSubject,
  deleteSubject,
  getSubjects,
  readError,
} from "../services/api.js";

export default function Subjects() {
  const navigate = useNavigate();

  const [subjects, setSubjects] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

  async function loadSubjects() {
    try {
      const response = await getSubjects();
      setSubjects(response.data);
    } catch (err) {
      setError(readError(err));
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createSubject(name, description);
      setName("");
      setDescription("");
      setShowModal(false);
      loadSubjects();
    } catch (err) {
      setError(readError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(event, subjectId) {
    event.stopPropagation(); // do not open the subject when deleting it
    if (!window.confirm("Delete this subject and all of its documents?")) return;
    try {
      await deleteSubject(subjectId);
      loadSubjects();
    } catch (err) {
      setError(readError(err));
    }
  }

  return (
    <div className="container page fade-up">
      <div className="page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>Subjects</h1>
          <p>Each subject keeps its own study material for RAG.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={17} /> New Subject
        </button>
      </div>

      {error && <div className="alert">{error}</div>}

      {subjects.length === 0 ? (
        <div className="glass empty">
          <h3>No subjects yet</h3>
          <p>Create your first subject, for example "Database Systems".</p>
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
                <button
                  className="btn btn-danger btn-sm"
                  onClick={(event) => handleDelete(event, subject.id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <Modal title="Create a subject" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate}>
            <div className="field">
              <label>Subject name</label>
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Database Systems"
                required
                autoFocus
              />
            </div>
            <div className="field">
              <label>Description (optional)</label>
              <input
                className="input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Semester 5 - DBMS course"
              />
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button className="btn btn-primary" disabled={saving}>
                {saving ? "Creating..." : "Create"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
