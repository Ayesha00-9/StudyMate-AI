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

---
---

# Part 2 — The new study features

Added after the first version. The original 19 answers above are still correct;
this part explains everything that is new.

---

## 20. Project Overview (short version for the examiner)

StudyMate AI is a study platform, not a general chatbot. A student uploads their own
lecture notes into a **subject**, and then chats with an AI tutor that answers from
those notes. On top of that they can generate quizzes, take exams, revise with
flashcards, read a summary, and track their progress and weak topics. Two guardrails
keep it study-focused and safe.

---

## 21. Frontend

React 18 built with Vite. Pages: Landing (with login), Register, Dashboard, Chat,
**Study Tools**, Subjects, Subject Detail. Routing is `react-router-dom`, HTTP calls
go through one file (`services/api.js`) using axios, and the login token is kept in
`localStorage`. Styling is plain CSS in `index.css` — dark theme with gradients and
glass panels. No state-management library is used; each page keeps its own `useState`.

---

## 22. Backend

FastAPI (Python). Each feature area is one router file inside `backend/routers/`.
The AI and RAG code lives in `backend/rag/`. `backend/guardrails.py` holds the two
safety/relevance checks. Everything is plain functions — no classes, no agents.

---

## 23. MongoDB

Five collections now: `users`, `subjects`, `documents`, `conversations` and the new
`quizzes`. A quiz document stores the generated questions **including** the correct
answer and the explanation, the student's answers, the score, and whether it was
submitted. Because the correct answers live on the server, the browser never sees
them until after Submit.

---

## 24. Authentication (all three ways)

```
Email + password        Google              Facebook
      │                    │                    │
      │              ID token from        access token from
      │              Google popup         Facebook popup
      │                    │                    │
      └────────────┬───────┴────────────────────┘
                   ▼
             FastAPI backend
      (verifies password OR verifies the provider token)
                   ▼
        find or create the user in MongoDB
                   ▼
              OUR OWN JWT
                   ▼
        Protected StudyMate API routes
```

The important point: **the JWT is always ours.** Google and Facebook are only used to
prove who the person is. After that moment, every request is authenticated exactly the
same way, with the same `get_current_user` dependency. Email/password login was not
changed at all.

---

## 25. JWT

Unchanged from Part 1: a signed token containing the user id (`sub`) and an expiry
(`exp`). The frontend stores it and sends `Authorization: Bearer <token>` with every
request.

---

## 26. Google OAuth — how it actually works here

1. The browser loads Google Identity Services and shows the "Continue with Google"
   button (`SocialLogin.jsx`).
2. The student signs in with Google. Google gives the **browser** an ID token.
3. The browser sends only that token to `POST /auth/google`.
4. The backend calls `https://oauth2.googleapis.com/tokeninfo` to verify it, and
   checks that `aud` (the audience) equals our `GOOGLE_CLIENT_ID` — this proves the
   token was issued for *our* app and not copied from somewhere else.
5. The backend finds the user by email, or creates a new one, and returns our JWT.

Only the public **client ID** is used in the frontend. The client secret stays in the
backend `.env`. (This flow verifies an ID token, so the secret is not strictly needed —
it is kept in the environment for the standard server-side flow.)

---

## 27. Facebook OAuth — how it actually works here

1. The browser loads the Facebook JS SDK and `FB.login()` opens the popup.
2. Facebook gives the browser an **access token**.
3. The browser sends it to `POST /auth/facebook`.
4. The backend calls `graph.facebook.com/debug_token` using
   `FACEBOOK_CLIENT_ID|FACEBOOK_CLIENT_SECRET` and checks `is_valid` **and** that
   `app_id` matches our app.
5. It then reads the profile from `graph.facebook.com/me` and returns our JWT.

Here the app secret really is required, and it is only ever used on the backend.
Facebook does not always give an email, so if it is missing we store a placeholder
address and match the user by their Facebook id instead.

**Avoiding duplicate accounts:** `find_or_create_social_user()` looks the student up by
email first, then by provider id. So signing in with Google and later with the same
email does not create two accounts.

---

## 28. Study Guardrail (Feature 1)

**Why:** StudyMate should not answer "write me a poem" — it is a study tool.

**How, in `guardrails.py`:**

1. The similarity search has already run. If the closest chunk from the student's own
   notes is very close (cosine distance ≤ **0.55**), the question is obviously about
   the subject → allowed, and no extra AI call happens.
2. Otherwise we ask GPT-4o-mini one tiny question: *"Is this question about studying
   <subject>? Answer YES or NO."* The prompt includes a few examples.
3. NO → the student gets:
   *"I'm here to help you study your selected subject. Please ask a question related to
   your subject or uploaded study material."*

**Why two thresholds?** `RELEVANCE_LIMIT = 0.75` in `chain.py` answers *"is this chunk
useful as context?"*. `STRONG_MATCH_LIMIT = 0.55` in `guardrails.py` answers *"is this
question definitely about the subject?"* — a stricter question needs a stricter number.
A loose match alone is not proof, so in that case we still ask the model.

**Why not keywords?** Because "What is DNS?" contains none of the words "network
security", yet it clearly belongs to that subject. The embedding search and the yes/no
check both understand meaning, not spelling.

---

## 29. Safety Guardrail (Feature 2)

Runs **first**, before retrieval and before any answer is generated. `guardrails.py`
matches the message against a list of self-harm phrases ("kill myself", "suicide",
"end my life", "want to die", …) with a regular expression. If it matches, the student
gets a short supportive message and the request never reaches GPT-4o-mini, so no
method, step or instruction can ever be produced.

Whole phrases are used, not single words, so ordinary security wording like "kill
chain" or "terminate a TCP connection" is not blocked by mistake.

---

## 30. Teach Me / Tutor Mode (Feature 3)

The same `/chat` route with `mode: "teach"`. When that flag is set, one extra system
message is added to the prompt asking for four fixed sections:

```
Simple Explanation
Important Points
Example
Quick Check
```

No new AI architecture — one extra instruction in the same prompt.

---

## 31. Quiz Generator (Feature 4)

1. `POST /study/quiz` takes a sample of the subject's chunks from ChromaDB.
2. One GPT-4o-mini call with `response_format={"type": "json_object"}` returns JSON:
   question, four options, `correct_index`, `explanation`, and a short `topic`.
3. The whole thing is saved in the `quizzes` collection.
4. The response to the browser contains **only** topic, question and options.
5. `POST /study/quiz/{id}/submit` compares the answers with the stored
   `correct_index`, returns the score, and shows the correct answer and explanation for
   every wrong question.

Asking for JSON means we get usable data straight away instead of text we would have
to parse ourselves.

---

## 32. Exam Mode (Feature 5)

Exactly the same code as the quiz, with `kind: "exam"` and 10 questions by default.
The frontend uses the same `QuizRunner` component with a different label. Nothing is
revealed until Submit. There was no reason to write the same screen twice.

---

## 33. Flashcards (Feature 6)

`GET /study/flashcards` asks GPT-4o-mini for JSON `{"cards": [{front, back}]}` built
from the subject's chunks. The React component keeps two pieces of state — which card
is showing and whether it is flipped — and the buttons are Previous, Flip and Next.

---

## 34. Study Summary (Feature 7)

`GET /study/summary` sends the subject's chunks with a prompt that forces four markdown
headings: **Main Concepts**, **Important Definitions**, **Key Points**,
**Exam-Focused Notes**. The prompt says "use ONLY the study material below", so the
summary comes from the notes and not from general knowledge.

---

## 35. Showing RAG to the student (Feature 8)

Every AI answer now carries a `status`:

| status | meaning | what the student sees |
| ------ | ------- | --------------------- |
| `rag` | answered from the uploaded notes | "Based on your uploaded study material" + `Source: file.pdf` |
| `general` | answered from general knowledge | normal bubble |
| `off_topic` | blocked by the study guardrail | amber "Study guardrail" badge |
| `safety` | blocked by the safety guardrail | amber "Safety guardrail" badge |

`sources` and `status` are also saved with the message in MongoDB, so reopening an old
chat still shows where the answer came from. This makes RAG visible during the demo.

---

## 36. Progress Dashboard (Feature 9)

`GET /study/progress` returns:

- **Questions Asked** — counted by looping over the student's conversations and
  counting messages with `role == "user"`.
- **Quizzes Completed** — submitted quizzes in the `quizzes` collection.
- **Average Score** — the mean percentage of those quizzes.
- **Uploaded Documents** — a `count_documents` on the documents collection.
- **Weak Topics** — see below.

Every single query filters on `user_id`, so one student can never see another
student's progress.

---

## 37. Weak Topics (Feature 10)

`find_weak_topics()` loops through the student's submitted quizzes, and for every
question where the chosen answer was not the correct one it adds 1 to a counter for
that question's `topic`. The topics are then sorted by how often they were missed and
the top 5 are returned.

**Practice Weak Topics** sends `practice_weak_topics: true` to `/study/quiz`. Instead
of taking a general sample of the material, the backend runs the normal similarity
search using the weak topic names as the query, so the new questions come from the
parts of the notes the student keeps getting wrong. This is the existing RAG system
being reused for a new purpose.

---

## 38. Deployment

- **Frontend → Vercel** (already deployed). Needs `VITE_API_URL`, and
  `VITE_GOOGLE_CLIENT_ID` / `VITE_FACEBOOK_APP_ID` if social login is used.
- **Backend → FastAPI Cloud** (already deployed). Needs the existing variables plus
  the four new OAuth ones, and `CORS_ORIGINS` must contain the Vercel URL.
- **Database → MongoDB Atlas.** No migration is needed — the new `quizzes` collection
  is created automatically the first time a quiz is generated.

---

## Extra questions the examiner may ask about the new features

**Why did you put the guardrails in a separate file?**
So the safety and relevance rules are in one obvious place instead of being buried
inside the chat route. It also makes them easy to test on their own.

**Doesn't the study guardrail cost an extra OpenAI call every time?**
No. If the question matches the uploaded notes closely, the check returns immediately
with no AI call. The extra call only happens when the match is weak or the subject has
no documents yet, and it asks for a single word so it is very cheap.

**What if the guardrail wrongly blocks a real study question?**
The threshold `STRONG_MATCH_LIMIT` and the examples in the prompt can be adjusted. The
code also fails open: if the check itself errors, the question is allowed through
rather than blocked.

**How do you stop the student seeing the quiz answers early?**
The correct answers are never sent to the browser. `QuizResponse` only contains topic,
question and options — the `correct_index` stays in MongoDB until Submit.

**Could a student submit someone else's quiz?**
No. The submit route looks up the quiz with `{"_id": quiz_id, "user_id": current_user}`,
so another user's quiz simply is not found (404).

**Is the safety check perfect?**
No — it is a phrase list, so unusual wording could get past it. It is a reasonable
first layer for a student project. A production system would add a moderation model as
a second layer. It is important to say this honestly rather than claim it is complete.

**Why does the safety check run before the study guardrail?**
Because a safety problem matters more than an off-topic problem. If someone writes
"I want to die", the right response is the supportive message — not "please ask about
your subject".
