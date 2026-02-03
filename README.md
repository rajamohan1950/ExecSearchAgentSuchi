# Suchi Executive Search Agent

Frontend (Next.js), API Gateway (FastAPI), and LinkedIn PDF parser services.

## Deploy frontend to Vercel (from GitHub)

Automatic deployments run on every push to your connected branch.

### 1. Connect the repo to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in (use **Continue with GitHub**).
2. Click **Add New…** → **Project**.
3. **Import** your Git repository (e.g. `mySuchiExecSearchAgent`).
4. Configure the project:
   - **Root Directory:** click **Edit**, choose `frontend`, then **Continue**.
   - **Framework Preset:** Next.js (auto-detected).
   - **Build Command:** `npm run build` (default).
   - **Output Directory:** leave default (Vercel uses `.next` for Next.js).
5. **Environment variables** (required for API proxy):
   - `NEXT_PUBLIC_API_URL` = your API base URL (e.g. `https://your-api.example.com`).
     - No trailing slash. The app rewrites `/api/v1/*` to this URL.
6. Click **Deploy**.

### 2. Automatic deployments

- **Production:** every push to `main` (or your default branch) deploys to production.
- **Preview:** every push to other branches or every pull request gets a preview URL.

You can change the production branch under **Project → Settings → Git**.

### 3. Optional: Vercel CLI

```bash
cd frontend
npm i -g vercel
vercel
```

Use the same **Root Directory** (`frontend`) when linking the project.
