// One subject: upload study material and see the files already uploaded.

import {
  ArrowLeft,
  FileText,
  MessagesSquare,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  deleteDocument,
  getDocuments,
  getSubject,
  readError,
  uploadDocument,
} from "../services/api.js";

export default function SubjectDetail() {
  const { subjectId } = useParams();
  const fileInputRef = useRef(null);

  const [subject, setSubject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadData();
  }, [subjectId]);

  async function loadData() {
    try {
      const [subjectResponse, documentsResponse] = await Promise.all([
        getSubject(subjectId),
        getDocuments(subjectId),
      ]);
      setSubject(subjectResponse.data);
      setDocuments(documentsResponse.data);
    } catch (err) {
      setError(readError(err));
    }
  }

  async function handleUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setError("");
    setSuccess("");
    try {
      const response = await uploadDocument(subjectId, file);
      setSuccess(
        `"${response.data.filename}" was processed into ${response.data.chunk_count} chunks.`
      );
      loadData();
    } catch (err) {
      setError(readError(err));
    } finally {
      setUploading(false);
      event.target.value = ""; // allow uploading the same file again
    }
  }

  async function handleDelete(documentId) {
    if (!window.confirm("Delete this document?")) return;
    try {
      await deleteDocument(documentId);
      loadData();
    } catch (err) {
      setError(readError(err));
    }
  }

  return (
    <div className="container page fade-up">
      <Link to="/subjects" className="btn btn-ghost btn-sm" style={{ marginBottom: 22 }}>
        <ArrowLeft size={15} /> All subjects
      </Link>

      <div
        className="page-head"
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}
      >
        <div>
          <h1>{subject ? subject.name : "Loading..."}</h1>
          <p>{subject?.description || "Upload your notes to use them in chat."}</p>
        </div>
        <Link to={`/chat?subject=${subjectId}`} className="btn btn-primary">
          <MessagesSquare size={17} /> Chat with this subject
        </Link>
      </div>

      {error && <div className="alert">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* ---- Upload box ---- */}
      <div
        className="dropzone"
        onClick={() => !uploading && fileInputRef.current.click()}
        style={{ marginBottom: 34 }}
      >
        <UploadCloud size={34} color="#8b5cf6" />
        <h4>{uploading ? "Processing your document..." : "Upload study material"}</h4>
        <p>
          {uploading
            ? "Extracting text, creating chunks and embeddings"
            : "Click to choose a PDF, DOCX or TXT file (max 10 MB)"}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.docx"
          onChange={handleUpload}
          style={{ display: "none" }}
        />
      </div>

      {/* ---- Uploaded files ---- */}
      <div className="section-head">
        <h2>Uploaded Documents ({documents.length})</h2>
      </div>

      {documents.length === 0 ? (
        <div className="glass empty">
          <h3>Nothing uploaded yet</h3>
          <p>Your notes will appear here once uploaded.</p>
        </div>
      ) : (
        documents.map((document) => (
          <div className="doc-row" key={document.id}>
            <FileText size={19} color="#22d3ee" />
            <div>
              <div className="name">{document.filename}</div>
              <div className="meta">
                {document.chunk_count} chunks ·{" "}
                {new Date(document.upload_date).toLocaleDateString()}
              </div>
            </div>
            <button
              className="btn btn-danger btn-sm"
              style={{ marginLeft: "auto" }}
              onClick={() => handleDelete(document.id)}
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))
      )}
    </div>
  );
}
