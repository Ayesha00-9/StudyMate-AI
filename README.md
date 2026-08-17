# StudyMate AI

**Study Smarter. Ask Better. Learn Faster.**
Your AI-powered study companion.

**Developer: Ayesha Amjad Ali**

---

## 1. Project Description

StudyMate AI is a complete AI chatbot web application built for students.

It works in two ways:

1. **Normal AI chat** — ask anything ("Explain TCP in simple words") and get an answer
   from OpenAI's GPT-4o-mini model.
2. **RAG chat** — create a subject, upload your own lecture notes (PDF / DOCX / TXT),
   and ask questions about them ("What is normalization according to my notes?").
   The application finds the matching parts of your documents and answers from them.

Every conversation is saved, so a student can come back to an old chat exactly like
in ChatGPT.

---

## 2. Features

- User registration, login and logout
- Password hashing (bcrypt) and JWT-protected API routes
- Multiple conversations with a sidebar of chat history
- Create and delete subjects (Database Systems, Computer Networks, ...)
- Upload study material per subject (PDF, DOCX, TXT)
- RAG answers with the source file names shown under the answer
- Normal AI conversation when no subject is selected
- Subject-specific context: one subject can never read another subject's documents
- Dashboard with statistics and recent conversations
- Dark, glassmorphism, 3D-inspired responsive interface

---

## 3. Technology Stack

| Layer          | Technology                                  |
| -------------- | ------------------------------------------- |
| Frontend       | React 18 + Vite, plain CSS, lucide-react     |
| Backend        | Python 3.10+ with FastAPI                   |
| Database       | MongoDB Atlas (via PyMongo)                 |
| Vector database| ChromaDB (stored on disk)                   |
| AI model       | OpenAI GPT-4o-mini                          |
| Embeddings     | OpenAI text-embedding-3-small               |
| Auth           | JWT (PyJWT) + bcrypt password hashing       |

---

## 4. Architecture

```
   React (Vite)                FastAPI (Python)              Storage
 ┌───────────────┐          ┌────────────────────┐      ┌──────────────────┐
 │  Landing      │          │  /auth/*           │      │  MongoDB Atlas   │
 │  Register     │  axios   │  /subjects         │─────▶│  users           │
 │  Dashboard    │ ───────▶ │  /documents/upload │      │  subjects        │
 │  Subjects     │  JWT in  │  /conversations    │      │  documents       │
 │  Chat         │  header  │  /chat             │      │  conversations   │
 └───────────────┘          └─────────┬──────────┘      └──────────────────┘
                                      │
                                      │ embeddings + similarity search
                                      ▼
                             ┌──────────────────┐        ┌──────────────┐
                             │    ChromaDB      │        │  OpenAI API  │
                             │ text chunks +    │        │ gpt-4o-mini  │
                             │ their embeddings │        │ embeddings   │
                             └──────────────────┘        └──────────────┘
```

**Two databases, two jobs.** MongoDB stores normal information (users, subjects,
file names, chat messages). ChromaDB stores only the document chunks and their
embeddings, because it is built for similarity search.

---

## 5. How RAG Works in This Project

RAG means **Retrieval Augmented Generation** — first *retrieve* the relevant text,
then let the AI *generate* an answer from it.

**When a document is uploaded** (`backend/rag/`):

```
PDF / DOCX / TXT file
        ↓  loader.py      extract the plain text
        ↓  splitter.py    cut it into ~1000-character overlapping chunks
        ↓  embeddings.py  turn every chunk into a vector with text-embedding-3-small
        ↓  vectorstore.py save chunk + vector + (user_id, subject_id, filename) in ChromaDB
```

**When the student asks a question** (`backend/rag/chain.py`):

```
Question
        ↓  turn the question into a vector too
        ↓  similarity search in ChromaDB, filtered by user_id AND subject_id
        ↓  keep only chunks whose cosine distance is below 0.75
        ↓  build a prompt: system rules + recent messages + chunks + question
        ↓  send it to GPT-4o-mini
        ↓  save the question and the answer in MongoDB
Answer  ←
```

If nothing relevant is found, the chatbot replies
*"I could not find this in your uploaded study material, but here is a general
explanation: ..."* so the student always knows where the answer came from.

**The RAG / normal-chat decision is intentionally simple:** if a subject is
selected in the chat, the documents of that subject are searched. If no subject is
selected, it is a normal GPT-4o-mini conversation. There is no AI agent deciding
this — just one `if` statement.

---

## 6. Folder Structure

```
studymate-ai/
├── backend/
│   ├── main.py                 FastAPI app, CORS, /stats route
│   ├── config.py               reads the .env file
│   ├── database.py             MongoDB connection and collections
│   ├── models.py               Pydantic request/response models
│   ├── auth.py                 password hashing, JWT, route protection
│   ├── routers/
│   │   ├── auth.py             /auth/register, /auth/login, /auth/me
│   │   ├── subjects.py         /subjects
│   │   ├── documents.py        /documents/upload
│   │   ├── conversations.py    /conversations (chat history)
│   │   └── chat.py             /chat  (the main chatbot route)
│   ├── rag/
│   │   ├── loader.py           read PDF / DOCX / TXT
│   │   ├── splitter.py         split text into chunks
│   │   ├── embeddings.py       OpenAI embeddings + shared OpenAI client
│   │   ├── vectorstore.py      ChromaDB: add and search chunks
│   │   └── chain.py            build the prompt and call GPT-4o-mini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/         Navbar, Modal, ChatMessage, ProtectedRoute
│   │   ├── pages/              Landing, Register, Dashboard, Subjects,
│   │   │                       SubjectDetail, Chat
│   │   ├── services/           api.js (all axios calls), auth.js (localStorage)
│   │   ├── App.jsx             routes
│   │   ├── main.jsx            entry point
│   │   └── index.css           the whole dark theme
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
├── README.md
├── VIVA_GUIDE.md
├── DEPLOYMENT.md
└── .gitignore
```

---

## 7. API Endpoints

| Method | Route                            | Description                        |
| ------ | -------------------------------- | ---------------------------------- |
| POST   | `/auth/register`                 | Create an account                  |
| POST   | `/auth/login`                    | Log in and get a JWT               |
| GET    | `/auth/me`                       | Current user (checks the token)    |
| POST   | `/auth/logout`                   | Logout                             |
| GET    | `/subjects`                      | List my subjects                   |
| POST   | `/subjects`                      | Create a subject                   |
| GET    | `/subjects/{subject_id}`         | One subject                        |
| DELETE | `/subjects/{subject_id}`         | Delete a subject + its documents   |
| POST   | `/documents/upload?subject_id=`  | Upload and process a document      |
| GET    | `/documents/{subject_id}`        | Documents of a subject             |
| DELETE | `/documents/{document_id}`       | Delete a document                  |
| GET    | `/conversations`                 | Chat history list (sidebar)        |
| POST   | `/conversations`                 | Create an empty conversation       |
| GET    | `/conversations/{id}`            | One conversation with its messages |
| DELETE | `/conversations/{id}`            | Delete a conversation              |
| POST   | `/chat`                          | Send a message, get the AI answer  |
| GET    | `/stats`                         | Dashboard numbers                  |

All routes except register and login require the header
`Authorization: Bearer <token>`.

Interactive documentation is generated automatically at
<http://localhost:8000/docs>.

---

## 8. MongoDB Collections

```
users          { name, email, password_hash, created_at }
subjects       { name, description, user_id, created_at }
documents      { filename, subject_id, user_id, upload_date, chunk_count }
conversations  { user_id, subject_id, title, messages[], created_at, updated_at }
```

A message inside `messages` looks like:
`{ role: "user" | "assistant", content: "...", created_at: "..." }`

Embeddings are **never** stored in MongoDB — they live in ChromaDB.

---

## 9. Environment Variables

`backend/.env` (copy from `backend/.env.example`):

```
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/
DATABASE_NAME=studymate
JWT_SECRET=some-long-random-string
JWT_EXPIRE_HOURS=24
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DIR=chroma_store
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

`frontend/.env` (copy from `frontend/.env.example`):

```
VITE_API_URL=http://localhost:8000
```

`.env` files are listed in `.gitignore` and must never be pushed to GitHub.

---

## 10. MongoDB Atlas Setup

1. Create a free account at <https://www.mongodb.com/atlas>.
2. Create a free **M0 cluster**.
3. **Database Access** → *Add New Database User* → note the username and password.
4. **Network Access** → *Add IP Address* → `0.0.0.0/0` (allow access from anywhere,
   fine for a student project).
5. **Connect** → *Drivers* → *Python* → copy the connection string and paste it into
   `MONGODB_URI` in `backend/.env`, replacing `<password>` with your real password.

The collections are created automatically the first time data is saved.

---

## 11. How to Run the Backend

```bash
cd backend

# create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

copy .env.example .env         # Windows   (cp on macOS/Linux)
# now open .env and fill in OPENAI_API_KEY and MONGODB_URI

uvicorn main:app --reload
```

Backend runs at <http://localhost:8000> — API docs at <http://localhost:8000/docs>.

---

## 12. How to Run the Frontend

```bash
cd frontend

npm install

copy .env.example .env         # Windows   (cp on macOS/Linux)

npm run dev
```

Frontend runs at <http://localhost:5173>.

Open it in the browser, create an account, add a subject, upload a PDF, and start
chatting.

---

## 13. Quick Test Walkthrough

1. Register a new account.
2. Go to **Subjects** → *New Subject* → "Database Systems".
3. Open the subject → upload `Normalization.pdf`.
4. Click **Chat with this subject**.
5. Ask *"What is normalization according to my notes?"* → the answer shows the file
   name it came from.
6. Start a **New Chat** with subject set to *General chat* and ask
   *"Explain TCP in simple words."* → a normal GPT-4o-mini answer.
7. Both chats now appear in the sidebar and survive a page refresh.

---

## 14. Future Improvements

- Streaming answers word by word
- Support for PPTX and image (OCR) study material
- Quiz and flashcard generation from the uploaded notes
- Sharing a subject with classmates
- Showing the exact page number of each source
- Refresh tokens and "forgot password" by email

---

## 15. Deployment

See **DEPLOYMENT.md** for the full step-by-step guide
(Frontend → Vercel, Backend → Render, Database → MongoDB Atlas).

---

**StudyMate AI — Your AI-powered study companion.**
Developed by **Ayesha Amjad Ali**.
