// One message bubble in the chat.
// AI answers are rendered as markdown so lists and bold text look nice.

import { FileText, Sparkles, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatMessage({ role, content, sources = [] }) {
  const isUser = role === "user";

  return (
    <div className={`message ${isUser ? "user" : ""}`}>
      <div className={`avatar ${isUser ? "me" : "ai"}`}>
        {isUser ? <User size={17} /> : <Sparkles size={17} />}
      </div>

      <div className={`bubble ${isUser ? "me" : "ai"}`}>
        {isUser ? content : <ReactMarkdown>{content}</ReactMarkdown>}

        {/* File names that the answer came from (only for RAG answers) */}
        {sources.length > 0 && (
          <div className="sources">
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
