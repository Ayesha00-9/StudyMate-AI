# StudyMate AI

**Study Smarter. Ask Better. Learn Faster.**
Your AI-powered study companion.

**Developer: Ayesha Amjad Ali**

---

## 1. Project Description

StudyMate AI is a complete AI study platform for students — not a general-purpose
chatbot.

A student creates a **subject** (for example "Network Security"), uploads their own
lecture notes (PDF / DOCX / TXT), and can then:

- **chat** with an AI tutor that answers from those notes (RAG),
- press **Teach Me** for a structured tutor-style explanation,
- generate a **quiz** or take an **exam** built from their own material,
- revise with **flashcards**,
- read a **study summary**,
- track **progress** and see which topics need practice.

Two guardrails keep the app study-focused and safe:

- The **study guardrail** politely refuses questions that are not about studying
  ("What is a biryani recipe?").
- The **safety guardrail** blocks self-harm requests before anything else runs.

---

## 2. Features

**Core (unchanged)**

- Registration, login, logout, bcrypt password hashing, JWT-protected routes
- Multiple conversations with a chat-history sidebar
- Subjects, each with their own uploaded documents
- RAG answers, with the source file name shown under the answer
- Subject isolation: one subject can never read another subject's documents

**New in this version**

| # | Feature | Where |
| - | ------- | ----- |
| 1 | Study guardrail (stay on the subject) | `backend/guardrails.py` |
| 2 | Safety guardrail (self-harm) | `backend/guardrails.py` |
| 3 | Teach Me / tutor mode | Chat page → "Teach Me" |
| 4 | Quiz generator (5 or 10 MCQs) | Study Tools → Generate Quiz |
| 5 | Exam mode | Study Tools → Exam Mode |
| 6 | Flashcards (Previous / Flip / Next) | Study Tools → Flashcards |
| 7 | Study summary (4 sections) | Study Tools → Summary |
| 8 | "Based on your uploaded study material" + Source | Chat and Study Tools |
| 9 | Progress dashboard | Dashboard → Study Progress |
| 10 | Weak topics + Practice Weak Topics | Dashboard → Needs Practice |
| 11 | Study-focused navigation | Navbar → Study Tools |
| 12 | Continue with Google | Login and Register pages |
| 13 | Continue with Facebook | Login and Register pages |

---

## 3. Technology Stack

| Layer           | Technology                                  |
| --------------- | ------------------------------------------- |
| Frontend        | React 18 + Vite, plain CSS, lucide-react     |
| Backend         | Python 3.11 with FastAPI                    |
| Database        | MongoDB Atlas (via PyMongo)                 |
| Vector database | ChromaDB (stored on disk)                   |
| AI model        | OpenAI GPT-4o-mini                          |
| Embeddings      | OpenAI text-embedding-3-small               |
| Auth            | JWT (PyJWT) + bcrypt, plus Google / Facebook |

---

## 4. Architecture

```
   React (Vite)                 FastAPI (Python)                 Storage
 ┌───────────────┐          ┌──────────────────────┐      ┌──────────────────┐
 │  Landing      │          │  /auth/*             │      │  MongoDB Atlas   │
 │  Register     │  axios   │  /auth/google        │─────▶│  users           │
 │  Dashboard    │ ───────▶ │  /auth/facebook      │      │  subjects        │
 │  Chat         │  JWT in  │  /subjects           │      │  documents       │
 │  Study Tools  │  header  │  /documents/upload   │      │  conversations   │
 │  Subjects     │          │  /conversations      │      │  quizzes         │
 └───────────────┘          │  /chat               │      └──────────────────┘
                            │  /study/*            │
                            └──────────┬───────────┘
                                       │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                 ┌──────────────────┐      ┌──────────────────┐
                 │    ChromaDB      │      │   OpenAI API     │
                 │ chunks + vectors │      │  gpt-4o-mini     │
                 │ per user+subject │      │  embeddings      │
                 └──────────────────┘      └──────────────────┘
```

**Two databases, two jobs.** MongoDB stores normal information (users, subjects, file
names, chat messages, quiz results). ChromaDB stores only the document chunks and
their embeddings, because it is built for similarity search.

---

## 5. How a chat message is handled

```
User question
      ↓
1. SAFETY GUARDRAIL        self-harm phrases -> supportive reply, stop here
      ↓
2. RETRIEVAL               similarity search in this subject's chunks (ChromaDB)
      ↓
3. STUDY GUARDRAIL         close match  -> allowed
                           weak / none  -> one YES/NO check with GPT-4o-mini
                           NO           -> "please ask about your subject", stop here
      ↓
4. PROMPT                  system rules + last 8 messages + retrieved chunks + question
      ↓
5. GPT-4o-mini             writes the answer
      ↓
6. SAVE                    question + answer + sources stored in MongoDB
```

Retrieval runs before the study guardrail on purpose: if the question already matches
the student's own notes, that is the strongest possible proof it is on-topic, and no
extra AI call is needed.

---

## 6. How RAG works

**When a document is uploaded** (`backend/rag/`):

```
PDF / DOCX / TXT
        ↓  loader.py      extract the plain text
        ↓  splitter.py    cut into ~1000-character overlapping chunks
        ↓  embeddings.py  one vector per chunk (text-embedding-3-small)
        ↓  vectorstore.py save chunk + vector + (user_id, subject_id, filename) in ChromaDB
```

**When a question is asked:**

```
Question -> vector -> similarity search filtered by user_id AND subject_id
         -> keep chunks with cosine distance <= 0.75
         -> put them in the prompt -> GPT-4o-mini -> answer + source file names
```

The quiz, flashcard and summary features do not have a question to search with, so
they take a general sample of the subject's chunks instead
(`get_subject_chunks` in `vectorstore.py`). "Practice Weak Topics" is the exception:
it uses the similarity search with the weak topic names as the query.

---

## 7. Folder Structure

```
studymate-ai/
├── backend/
│   ├── main.py                 FastAPI app, CORS, /stats
│   ├── config.py               reads .env (now also the OAuth ids)
│   ├── database.py             MongoDB collections (now also "quizzes")
│   ├── models.py               request / response models
│   ├── auth.py                 password hashing, JWT, route protection
│   ├── guardrails.py           NEW - safety guardrail + study guardrail
│   ├── routers/
│   │   ├── auth.py             register, login, /auth/google, /auth/facebook
│   │   ├── subjects.py
│   │   ├── documents.py
│   │   ├── conversations.py
│   │   ├── chat.py             the main chatbot route
│   │   └── study.py            NEW - quiz, exam, flashcards, summary, progress
│   ├── rag/
│   │   ├── loader.py           read PDF / DOCX / TXT
│   │   ├── splitter.py         split text into chunks
│   │   ├── embeddings.py       OpenAI embeddings + shared OpenAI client
│   │   ├── vectorstore.py      ChromaDB: add, search, sample, delete
│   │   ├── chain.py            guardrails + prompt + GPT-4o-mini
│   │   └── study_tools.py      NEW - quiz / flashcard / summary generation
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/         Navbar, Modal, ChatMessage, ProtectedRoute,
│   │   │                       SocialLogin, QuizRunner, FlashcardDeck
│   │   ├── pages/              Landing, Register, Dashboard, Chat,
│   │   │                       Study, Subjects, SubjectDetail
│   │   ├── services/           api.js, auth.js
│   │   ├── App.jsx  main.jsx  index.css
│   ├── vite.config.js  package.json  .env.example
├── README.md
├── VIVA_GUIDE.md
├── DEPLOYMENT.md
└── .gitignore
```

---

## 8. API Endpoints

| Method | Route | Description |
| ------ | ----- | ----------- |
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in and get a JWT |
| POST | `/auth/google` | **New** – verify a Google ID token, return our JWT |
| POST | `/auth/facebook` | **New** – verify a Facebook token, return our JWT |
| GET | `/auth/me` | Current user |
| POST | `/auth/logout` | Logout |
| GET / POST | `/subjects` | List / create subjects |
| GET / DELETE | `/subjects/{id}` | One subject / delete it |
| POST | `/documents/upload?subject_id=` | Upload and process a document |
| GET | `/documents/{subject_id}` | Documents of a subject |
| DELETE | `/documents/{document_id}` | Delete a document |
| GET / POST | `/conversations` | Chat history / new conversation |
| GET / DELETE | `/conversations/{id}` | One conversation / delete it |
| POST | `/chat` | Send a message (`mode` = `chat` or `teach`) |
| POST | `/study/quiz` | **New** – generate a quiz or exam |
| POST | `/study/quiz/{quiz_id}/submit` | **New** – mark the answers |
| GET | `/study/flashcards?subject_id=` | **New** – flashcards |
| GET | `/study/summary?subject_id=` | **New** – study summary |
| GET | `/study/progress` | **New** – progress + weak topics |
| GET | `/stats` | Dashboard numbers |

Everything except register / login / google / facebook needs the header
`Authorization: Bearer <token>`.
Interactive docs: <http://localhost:8000/docs>.

---

## 9. MongoDB Collections

```
users          { name, email, password_hash, auth_provider?, provider_id?, created_at }
subjects       { name, description, user_id, created_at }
documents      { filename, subject_id, user_id, upload_date, chunk_count }
conversations  { user_id, subject_id, title, messages[], created_at, updated_at }
quizzes        { user_id, subject_id, kind, questions[], answers[], score,
                 submitted, created_at, submitted_at }        <-- NEW
```

`quizzes` is the only new collection. Nothing had to be changed in the existing four —
`password_hash` is simply `null` for accounts created with Google or Facebook, and
`messages` now also carries `sources` and `status` on AI messages (old messages
without those fields still work).

Embeddings are **never** stored in MongoDB — they live in ChromaDB.

---

## 10. Environment Variables

`backend/.env` (copy from `backend/.env.example`):

```
OPENAI_API_KEY=
MONGODB_URI=
DATABASE_NAME=studymate
JWT_SECRET=
JWT_EXPIRE_HOURS=24
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DIR=chroma_store
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# new, optional - leave empty to keep only email/password login
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=
```

`frontend/.env` (copy from `frontend/.env.example`):

```
VITE_API_URL=http://localhost:8000

# new, optional - only the PUBLIC ids, never a secret
VITE_GOOGLE_CLIENT_ID=
VITE_FACEBOOK_APP_ID=
```

If the social variables are empty, the buttons simply do not appear and everything
else works exactly as before.

**Never put a real key in `.env.example`** — that file is committed to GitHub.

---

## 11. How to Run

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env           # then fill in your keys
uvicorn main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Backend: <http://localhost:8000> · Frontend: <http://localhost:5173>

---

## 12. Future Improvements

- Streaming answers word by word
- PPTX and scanned-image (OCR) study material
- Spaced repetition for the flashcards
- Progress charts over time
- Sharing a subject with classmates

---

## 13. Deployment

Already deployed: **Frontend → Vercel**, **Backend → FastAPI Cloud**,
**Database → MongoDB Atlas**. See `DEPLOYMENT.md` for what to update when pushing
this version.

---

**StudyMate AI — Your AI-powered study companion.**
Developed by **Ayesha Amjad Ali**.
