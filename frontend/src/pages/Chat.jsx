// The chat page: conversation sidebar, messages and the input box.

import { GraduationCap, MessageSquarePlus, Send, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import ChatMessage from "../components/ChatMessage.jsx";
import {
  deleteConversation,
  getConversation,
  getConversations,
  getSubjects,
  readError,
  sendChatMessage,
} from "../services/api.js";

const SUGGESTIONS = [
  "What is network security?",
  "What is normalization according to my notes?",
  "Explain TCP/IP.",
  "Summarise my uploaded lecture in bullet points.",
];

export default function Chat() {
  const [searchParams] = useSearchParams();

  const [subjects, setSubjects] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(searchParams.get("conversation") || null);
  const [subjectId, setSubjectId] = useState(searchParams.get("subject") || "");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  // Teach Me mode: the backend answers with Explanation / Points / Example / Quick Check.
  const [teachMode, setTeachMode] = useState(false);

  const bottomRef = useRef(null);

  // Load the sidebar data once.
  useEffect(() => {
    loadSubjects();
    loadConversations();
  }, []);

  // Whenever a different conversation is selected, load its messages.
  useEffect(() => {
    if (activeId) {
      openConversation(activeId);
    } else {
      setMessages([]);
    }
  }, [activeId]);

  // Always scroll to the newest message.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function loadSubjects() {
    try {
      const response = await getSubjects();
      setSubjects(response.data);
    } catch (err) {
      setError(readError(err));
    }
  }

  async function loadConversations() {
    try {
      const response = await getConversations();
      setConversations(response.data);
    } catch (err) {
      setError(readError(err));
    }
  }

  async function openConversation(conversationId) {
    try {
      const response = await getConversation(conversationId);
      setMessages(response.data.messages);
      setSubjectId(response.data.subject_id || "");
    } catch (err) {
      setError(readError(err));
    }
  }

  function startNewChat() {
    setActiveId(null);
    setMessages([]);
    setError("");
  }

  async function handleDeleteConversation(event, conversationId) {
    event.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await deleteConversation(conversationId);
      if (conversationId === activeId) startNewChat();
      loadConversations();
    } catch (err) {
      setError(readError(err));
    }
  }

  async function handleSend(text) {
    const question = (text ?? input).trim();
    if (!question || sending) return;

    setInput("");
    setError("");
    // Show the user's message straight away so the chat feels fast.
    setMessages((previous) => [
      ...previous,
      { role: "user", content: question, created_at: new Date().toISOString() },
    ]);
    setSending(true);

    try {
      const response = await sendChatMessage(
        question,
        activeId,
        subjectId || null,
        teachMode ? "teach" : "chat"
      );
      const { answer, conversation_id, sources, status } = response.data;

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: answer,
          sources,
          status,
          created_at: new Date().toISOString(),
        },
      ]);

      if (!activeId) setActiveId(conversation_id);
      loadConversations();
    } catch (err) {
      setError(readError(err));
      // The message was never saved on the server, so take it back off the
      // screen and put the text back in the box for the student to retry.
      setMessages((previous) => previous.slice(0, -1));
      setInput(question);
    } finally {
      setSending(false);
    }
  }

  // Enter sends the message, Shift+Enter makes a new line.
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  const activeSubject = subjects.find((subject) => subject.id === subjectId);

  return (
    <div className="chat-layout">
      {/* ---------- Sidebar ---------- */}
      <aside className="chat-sidebar">
        <button className="btn btn-primary btn-block" onClick={startNewChat}>
          <MessageSquarePlus size={17} /> New Chat
        </button>

        <div>
          <div className="sidebar-label" style={{ marginBottom: 8 }}>
            Subject context
          </div>
          <select
            className="input"
            value={subjectId}
            onChange={(event) => setSubjectId(event.target.value)}
          >
            <option value="">General chat (no documents)</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
        </div>

        <div className="sidebar-label">Your chats</div>
        <div className="conv-list">
          {conversations.length === 0 && (
            <p style={{ fontSize: 13, color: "var(--text-faint)" }}>No chats yet.</p>
          )}
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conv-item ${conversation.id === activeId ? "active" : ""}`}
              onClick={() => setActiveId(conversation.id)}
            >
              <span className="conv-title">{conversation.title}</span>
              <button
                className="conv-delete"
                onClick={(event) => handleDeleteConversation(event, conversation.id)}
                title="Delete chat"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* ---------- Main chat area ---------- */}
      <section className="chat-main">
        <div className="chat-header">
          <div>
            <h3>StudyMate AI</h3>
            <div className="sub">
              {activeSubject
                ? `Answering from "${activeSubject.name}" documents`
                : "General study mode - no subject selected"}
            </div>
          </div>
          {activeSubject && (
            <span className="badge">
              <Sparkles size={12} /> RAG enabled
            </span>
          )}
        </div>

        <div className="messages">
          {messages.length === 0 && !sending ? (
            <div className="chat-welcome">
              <div className="big-mark">
                <Sparkles size={30} color="#fff" />
              </div>
              <h2>
                How can I help you <span className="gradient-text">study</span> today?
              </h2>
              <p>
                Ask a study question, or pick a subject on the left to get answers from
                your own uploaded notes.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    className="suggestion"
                    key={suggestion}
                    onClick={() => handleSend(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <ChatMessage
                key={index}
                role={message.role}
                content={message.content}
                sources={message.sources || []}
                status={message.status || ""}
              />
            ))
          )}

          {sending && (
            <div className="message">
              <div className="avatar ai">
                <Sparkles size={17} />
              </div>
              <div className="bubble ai">
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="composer">
          {error && <div className="alert">{error}</div>}

          {/* Teach Me: same chat, but the AI replies as a tutor with
              Simple Explanation / Important Points / Example / Quick Check. */}
          <button
            className={`teach-toggle ${teachMode ? "on" : ""}`}
            onClick={() => setTeachMode(!teachMode)}
            title="Answer like a tutor: explanation, points, example and a quick check question"
          >
            <GraduationCap size={15} />
            Teach Me {teachMode ? "· on" : ""}
          </button>

          <div className="composer-box">
            <textarea
              rows={1}
              value={input}
              placeholder={
                teachMode
                  ? "Which topic should I teach you? e.g. Teach me TCP/IP"
                  : "Ask a question about your subject..."
              }
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="send-btn"
              onClick={() => handleSend()}
              disabled={sending || !input.trim()}
            >
              <Send size={18} />
            </button>
          </div>
          <div className="composer-hint">
            Press Enter to send · Shift + Enter for a new line
          </div>
        </div>
      </section>
    </div>
  );
}
