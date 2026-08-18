// All calls to the FastAPI backend happen through this file.
// Using one place makes it easy to change the server address later.

import axios from "axios";

// The address comes from the .env file, so it can change per environment.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

// Before every request, attach the saved login token.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token is rejected, send the user back to the login page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/") window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// ---------- Auth ----------
export const registerUser = (name, email, password) =>
  api.post("/auth/register", { name, email, password });

export const loginUser = (email, password) =>
  api.post("/auth/login", { email, password });

// Social login: we send the token from Google/Facebook and get OUR JWT back.
export const loginWithGoogle = (token) => api.post("/auth/google", { token });
export const loginWithFacebook = (token) => api.post("/auth/facebook", { token });

// ---------- Subjects ----------
export const getSubjects = () => api.get("/subjects");
export const getSubject = (id) => api.get(`/subjects/${id}`);
export const createSubject = (name, description) =>
  api.post("/subjects", { name, description });
export const deleteSubject = (id) => api.delete(`/subjects/${id}`);

// ---------- Documents ----------
export const getDocuments = (subjectId) => api.get(`/documents/${subjectId}`);
export const uploadDocument = (subjectId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post(`/documents/upload?subject_id=${subjectId}`, formData);
};
export const deleteDocument = (id) => api.delete(`/documents/${id}`);

// ---------- Conversations ----------
export const getConversations = () => api.get("/conversations");
export const getConversation = (id) => api.get(`/conversations/${id}`);
export const deleteConversation = (id) => api.delete(`/conversations/${id}`);

// ---------- Chat ----------
// mode is "chat" normally, or "teach" when the Teach Me button is used.
export const sendChatMessage = (message, conversationId, subjectId, mode = "chat") =>
  api.post("/chat", {
    message,
    conversation_id: conversationId || null,
    subject_id: subjectId || null,
    mode,
  });

// ---------- Study tools ----------
export const createQuiz = (subjectId, count, kind, practiceWeakTopics = false) =>
  api.post("/study/quiz", {
    subject_id: subjectId,
    count,
    kind,
    practice_weak_topics: practiceWeakTopics,
  });

export const submitQuiz = (quizId, answers) =>
  api.post(`/study/quiz/${quizId}/submit`, { answers });

export const getFlashcards = (subjectId, count = 8) =>
  api.get(`/study/flashcards?subject_id=${subjectId}&count=${count}`);

export const getSummary = (subjectId) =>
  api.get(`/study/summary?subject_id=${subjectId}`);

export const getProgress = () => api.get("/study/progress");

// ---------- Dashboard ----------
export const getStats = () => api.get("/stats");

// Turns any backend error into a readable sentence for the user.
export const readError = (error) =>
  error?.response?.data?.detail || error?.message || "Something went wrong";

export default api;
