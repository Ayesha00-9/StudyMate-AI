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
export const sendChatMessage = (message, conversationId, subjectId) =>
  api.post("/chat", {
    message,
    conversation_id: conversationId || null,
    subject_id: subjectId || null,
  });

// ---------- Dashboard ----------
export const getStats = () => api.get("/stats");

// Turns any backend error into a readable sentence for the user.
export const readError = (error) =>
  error?.response?.data?.detail || error?.message || "Something went wrong";

export default api;
