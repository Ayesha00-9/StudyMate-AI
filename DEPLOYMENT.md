# Deploying StudyMate AI

Do this **after** everything works on your own computer.

```
Frontend  → Vercel
Backend   → Render (free Python web service)
Database  → MongoDB Atlas (already in the cloud)
Vectors   → ChromaDB folder on the backend's persistent disk
```

---

## Step 0 — Push the code to GitHub

```bash
cd studymate-ai
git init
git add .
git commit -m "StudyMate AI"
git branch -M main
git remote add origin https://github.com/<your-username>/studymate-ai.git
git push -u origin main
```

Check that `.env` files were **not** uploaded — only `.env.example` should be there.

---

## Step 1 — MongoDB Atlas

Already cloud-hosted. Just make sure:

- **Network Access** allows `0.0.0.0/0` so the deployed backend can connect.
- You have the connection string ready.

---

## Step 2 — Backend on Render

1. Go to <https://render.com> → **New** → **Web Service** → connect your GitHub repo.
2. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Environment variables** (Render dashboard → Environment):

   | Key | Value |
   | --- | --- |
   | `OPENAI_API_KEY` | your OpenAI key |
   | `MONGODB_URI` | your Atlas connection string |
   | `DATABASE_NAME` | `studymate` |
   | `JWT_SECRET` | a long random string |
   | `CHROMA_DIR` | `/var/data/chroma_store` |
   | `CORS_ORIGINS` | your Vercel URL, e.g. `https://studymate-ai.vercel.app` |

4. **Add a Disk** (Render → Disks): mount path `/var/data`, size 1 GB.
   This keeps the ChromaDB vectors when the service restarts.
5. Deploy. Open `https://<your-backend>.onrender.com/docs` to check it is alive.

> Note: on Render's free plan the service sleeps when idle, so the very first
> request after a break can take ~30 seconds.

---

## Step 3 — Frontend on Vercel

1. Go to <https://vercel.com> → **Add New Project** → import the same repo.
2. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. **Environment variable:**

   | Key | Value |
   | --- | --- |
   | `VITE_API_URL` | `https://<your-backend>.onrender.com` |

4. Deploy.

---

## Step 4 — Connect the two

Go back to Render and make sure `CORS_ORIGINS` contains your exact Vercel URL
(no trailing slash), then redeploy the backend.

---

## Step 5 — Test the live app

1. Open the Vercel URL.
2. Register a new account.
3. Create a subject and upload a small PDF.
4. Ask a question about it — you should see the source file name under the answer.

---

## Common problems

| Problem | Cause | Fix |
| --- | --- | --- |
| `CORS error` in the browser console | Vercel URL missing in `CORS_ORIGINS` | add it on Render and redeploy |
| `Network Error` on login | `VITE_API_URL` wrong or backend asleep | check the value, open `/docs` first |
| Uploads work but answers say "not found" after a redeploy | ChromaDB folder was wiped | make sure the persistent disk is attached and `CHROMA_DIR` points to it |
| `pymongo ServerSelectionTimeoutError` | Atlas IP whitelist | allow `0.0.0.0/0` in Network Access |
| 401 on every request | `JWT_SECRET` changed | old tokens are invalid — log in again |

---

**StudyMate AI** — by Ayesha Amjad Ali.
