# StudyMate AI — Viva Guide

Simple answers to the questions you are most likely to be asked.
**Ayesha Amjad Ali**

---

### 1. What is FastAPI?

FastAPI is a modern Python framework for building web APIs. You write a normal
Python function, put a decorator like `@router.post("/chat")` on top of it, and it
becomes an API endpoint. It also validates the incoming data automatically using
Pydantic models and generates interactive documentation at `/docs` for free.

---

### 2. Why did you choose Python?

Because the AI part of the project is much easier in Python. The official OpenAI
library, ChromaDB, PyPDF and python-docx are all Python-first tools. Writing the RAG
pipeline in Python took a few short files instead of fighting with wrappers in
another language.

---

### 3. Why not Node.js?

Node.js is excellent for normal web APIs, but the AI and vector-database ecosystem
is stronger in Python. Document parsing, embeddings and ChromaDB all have mature,
well-documented Python support. Since my project is mainly about RAG, Python was the
simpler and safer choice. (The frontend still uses Node tooling — Vite — but the
backend is fully Python.)

---

### 4. What is MongoDB?

MongoDB is a NoSQL document database. Instead of tables and rows it stores
JSON-like documents. A user record looks almost exactly like a JSON object, which
makes it very natural to use with a web application.

---

### 5. Why MongoDB?

- My data is JSON-shaped, especially a conversation which contains a whole list of
  messages inside one document — that would need an extra table in SQL.
- The schema is flexible, so I could add fields like `chunk_count` without a
  migration.
- MongoDB Atlas gives a free cloud cluster, so the project works from anywhere and
  is ready for deployment.

---

### 6. What is ChromaDB?

ChromaDB is an open-source **vector database**. It stores pieces of text together
with their embeddings (lists of numbers) and can find the pieces whose meaning is
closest to a question. In this project it saves the vectors to a folder on disk, so
nothing extra needs to be installed or run.

---

### 7. Why do we need ChromaDB?

MongoDB can find text that *matches keywords*. It cannot find text that has a
*similar meaning*. If a student asks "how do we remove redundancy from tables?" the
notes might say "normalization reduces duplicate data" — no keyword matches, but the
meaning does. ChromaDB compares embeddings, so it finds that chunk. That is exactly
what RAG needs.

---

### 8. What are embeddings?

An embedding is a list of numbers (a vector) that represents the *meaning* of a
piece of text. Texts with similar meanings get vectors that point in a similar
direction. We measure how close two vectors are using **cosine distance**: 0 means
almost the same meaning, close to 1 means unrelated. I use OpenAI's
`text-embedding-3-small` model to create them.

---

### 9. What is RAG?

RAG stands for **Retrieval Augmented Generation**. Instead of hoping the AI already
knows the answer, we first *retrieve* the relevant parts of the user's own documents
and paste them into the prompt. The AI then *generates* the answer using that text.
It makes answers specific to the student's own notes and reduces made-up answers.

---

### 10. How does RAG work?

```
Document → extract text → split into chunks → create embeddings → store in ChromaDB
Question → create embedding → similarity search → get top matching chunks
        → prompt = chunks + recent messages + question → GPT-4o-mini → answer
```

Two phases: an **indexing** phase that happens once when the file is uploaded, and a
**query** phase that happens on every question.

---

### 11. What happens when a PDF is uploaded?

1. The file goes to `POST /documents/upload?subject_id=...`.
2. `rag/loader.py` reads the PDF with PyPDF and extracts the plain text.
3. `rag/splitter.py` cuts the text into ~1000-character chunks with a 150-character
   overlap so sentences are not broken.
4. `rag/embeddings.py` sends all chunks to OpenAI and gets one embedding per chunk.
5. `rag/vectorstore.py` saves each chunk + embedding in ChromaDB, tagged with
   `user_id`, `subject_id`, `document_id` and `filename`.
6. Only the file details (name, subject, date, chunk count) are saved in MongoDB.

---

### 12. What happens when a user asks a question?

1. The frontend calls `POST /chat` with the message, the conversation id and the
   selected subject id.
2. The backend checks the JWT and loads that conversation from MongoDB.
3. If a subject is selected, it embeds the question and does a similarity search in
   ChromaDB filtered by `user_id` and `subject_id`.
4. Chunks whose cosine distance is under 0.75 are kept as context.
5. A prompt is built: system instructions + the last 8 messages + the retrieved
   chunks + the question.
6. GPT-4o-mini generates the answer.
7. The question and answer are pushed into the conversation's `messages` array in
   MongoDB and the answer is returned to the frontend.

---

### 13. What does GPT-4o-mini do?

It is the language model that actually writes the answer. It is a smaller, cheaper
and faster version of GPT-4o, which is perfect for a student project. It does two
jobs here: normal conversation, and turning the retrieved chunks into a clear
explanation.

---

### 14. How is chat history stored?

In the `conversations` collection in MongoDB. One document per conversation:

```json
{
  "user_id": "...",
  "subject_id": "...",
  "title": "DBMS Exam Preparation",
  "messages": [
    { "role": "user", "content": "What is normalization?", "created_at": "..." },
    { "role": "assistant", "content": "Normalization is...", "created_at": "..." }
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

Every new message is appended with MongoDB's `$push`. The sidebar lists these
conversations sorted by `updated_at`, so the newest chat is on top. The title is
made automatically from the first question.

---

### 15. How does subject-specific RAG work?

Every chunk stored in ChromaDB carries metadata: `user_id`, `subject_id`,
`document_id`, `filename`. When searching I pass a `where` filter:

```python
where={"$and": [{"user_id": user_id}, {"subject_id": subject_id}]}
```

So the search can only ever return chunks that belong to this user **and** this
subject. Asking a Computer Networks question can never pull in Database Systems
notes, and no user can see another user's documents.

---

### 16. How does the frontend communicate with the backend?

Through HTTP requests using **axios**. All the calls live in
`frontend/src/services/api.js`. The base URL comes from the `VITE_API_URL`
environment variable, so it can point to localhost during development and to the
deployed server in production. An axios *interceptor* automatically attaches the
header `Authorization: Bearer <token>` to every request. Because the frontend
(port 5173) and the backend (port 8000) are different origins, the backend enables
**CORS** middleware to allow those requests.

---

### 17. How are passwords protected?

Passwords are never stored. When a user registers, `auth.py` runs
`bcrypt.hashpw(password, bcrypt.gensalt())` and stores only the resulting hash.
Bcrypt is a one-way hashing function with a random salt, so two users with the same
password get different hashes and the original cannot be recovered. At login,
`bcrypt.checkpw()` compares the typed password against the stored hash.

After a successful login the server returns a **JWT** — a signed token containing
the user id and an expiry time. The frontend saves it in localStorage and sends it
with every request. Protected routes use the `get_current_user` dependency, which
verifies the signature and loads the user; if the token is missing, wrong or
expired, the API replies 401.

---

### 18. Where are API keys stored?

In the `backend/.env` file, which is loaded by `python-dotenv` in `config.py`.
Nothing is hardcoded, and `.env` is listed in `.gitignore` so it is never pushed to
GitHub. The repository only contains `.env.example` with empty values. In production
the same values are set as environment variables in the hosting dashboard.

---

### 19. How will the application be deployed?

- **Frontend → Vercel.** Vercel builds the Vite project and serves the static files.
  `VITE_API_URL` is set in the Vercel dashboard to the live backend URL.
- **Backend → Render** (or Railway). It runs
  `uvicorn main:app --host 0.0.0.0 --port $PORT`, with `OPENAI_API_KEY`,
  `MONGODB_URI`, `JWT_SECRET` and `CORS_ORIGINS` set as environment variables.
  A persistent disk is attached so the ChromaDB folder survives restarts.
- **Database → MongoDB Atlas**, which is already cloud-hosted.

Full steps are in `DEPLOYMENT.md`.

---

## Bonus questions the examiner may add

**Why do you split documents into chunks?**
A whole PDF is far too long to fit in a prompt, and sending everything would be slow
and expensive. Small chunks let us send only the few paragraphs that actually answer
the question.

**Why is there an overlap between chunks?**
So a sentence or definition that falls exactly on a boundary is not cut in half and
lost.

**What is the "top_k" in the search?**
The number of closest chunks we take. I use 4 — enough context without making the
prompt huge.

**What happens if the answer is not in the notes?**
No chunk passes the 0.75 distance limit, so the model is told to start its reply
with "I could not find this in your uploaded study material..." and then answer from
general knowledge. The student always knows the source.

**Why do you only send the last 8 messages?**
To keep the prompt small, fast and cheap. Sending an entire long conversation every
time would waste tokens.

**What is a JWT made of?**
Three parts: a header, a payload (here: the user id `sub` and the expiry `exp`) and
a signature created with the secret key. The server can verify it without storing
any session in the database.

**Why is logout handled on the frontend?**
Because JWTs are stateless — the server keeps no session. Deleting the token from
localStorage means the browser can no longer prove who it is, which is exactly what
logging out means.
