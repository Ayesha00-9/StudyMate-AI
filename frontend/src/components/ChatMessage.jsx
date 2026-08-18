// One message bubble in the chat.
// AI answers are rendered as markdown so lists and bold text look nice.

import { FileText, Shield, Sparkles, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatMessage({ role, content, sources = [], status = "" }) {
  const isUser = role === "user";

  // The guardrail answers get their own look so they stand out.
  const isGuardrail = status === "safety" || status === "off_topic";

  return (
    <div className={`message ${isUser ? "user" : ""}`}>
      <div className={`avatar ${isUser ? "me" : "ai"}`}>
        {isUser ? <User size={17} /> : <Sparkles size={17} />}
      </div>

      <div className={`bubble ${isUser ? "me" : "ai"} ${isGuardrail ? "guardrail" : ""}`}>
        {/* Feature 8: make RAG visible to the student */}
        {status === "rag" && (
          <div className="rag-banner">
            <FileText size={12} /> Based on your uploaded study material
          </div>
        )}

        {isGuardrail && (
          <div className="rag-banner guard">
            <Shield size={12} />
            {status === "safety" ? "Safety guardrail" : "Study guardrail"}
          </div>
        )}

        {isUser ? content : <ReactMarkdown>{content}</ReactMarkdown>}

        {/* File names that the answer came from (only for RAG answers) */}
        {sources.length > 0 && (
          <div className="sources">
            <span className="sources-label">Source:</span>
            {sources.map((source) => (
              <span className="source-chip" key={source}>
                <FileText size={11} /> {source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
