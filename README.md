# AI GitHub Repo Scanner

Paste a public GitHub link. Seven small agents download the repo, check it with rules, review it with Gemini models, double-check the review with a second model, and show a score out of 100 with a PDF report.

- Frontend: Next.js + Tailwind CSS (`frontend/`)
- Backend: Python + FastAPI (`backend/`)
- AI: Google Gemini API (small model, strong model, validator model)

## How to run

You need Python 3.12 or newer, Node.js, Git and a Gemini API key (free from https://aistudio.google.com/apikey).

**1. Backend** (first terminal)

```powershell
cd D:\Mayank\reposcanner\backend
copy .env.example .env
```

Open `backend\.env` and paste your Gemini key after `GEMINI_API_KEY=`. Then:

```powershell
.\venv\Scripts\uvicorn main:app --reload --port 8000
```

If the `venv` folder is missing, create it first: `python -m venv venv`, then `.\venv\Scripts\pip install -r requirements.txt`.

**2. Frontend** (second terminal)

```powershell
cd D:\Mayank\reposcanner\frontend
npm install
npm run dev
```

Open http://localhost:3000, paste a link like `https://github.com/owner/repo` and press **Scan repo**.

**Tests** (no Gemini key needed, the AI is faked): `cd backend`, then `.\venv\Scripts\pip install -r requirements-dev.txt` once, then `.\venv\Scripts\python -m pytest`.

## Deploy (Vercel for the website, Render for the backend)

Push the whole `reposcanner` folder to one GitHub repository first. The backend goes up first because the website needs its address.

**1. Backend on Render**

1. In Render choose **New > Blueprint**, pick your repository. Render reads `render.yaml` and creates the `reposcanner-api` web service (Docker, free plan). The `backend/Dockerfile` installs Git, which the Fetcher Agent needs.
2. When asked, fill the two secret values: `GEMINI_API_KEY` (your key) and `FRONTEND_URL` (type `http://localhost:3000` for now, you change it in step 3).
3. After the deploy finishes, open `https://<your-service>.onrender.com/health`. It must show `{"status":"ok"}`. Copy this address.

**2. Website on Vercel**

1. In Vercel choose **Add New > Project**, import the same repository.
2. Set **Root Directory** to `frontend`. Vercel detects Next.js by itself.
3. Add one environment variable: `NEXT_PUBLIC_API_URL` = the Render address from step 1 (no slash at the end).
4. Deploy and copy the Vercel address.

**3. Connect them**

In Render open the service, go to **Environment**, and set `FRONTEND_URL` to your Vercel address (for example `https://reposcanner.vercel.app`). You can give several addresses separated by commas. Render redeploys by itself. Now open the Vercel site and scan a repo.

Good to know:

- The free Render service sleeps after 15 minutes without visits and takes about a minute to wake up. The website pings it as soon as the page opens, and the progress screen tells you when it is waking up. Open the site a minute before the presentation.
- A scan runs in the background on the server. The website asks every second what the agents have finished, which is why the agent log appears live and no request ever stays open for minutes.
- Scan jobs are kept in the memory of the one running server, so the service must run a single instance (the free plan does). A restart clears them.
- Anyone who knows your website address can run scans with your Gemini key. The free tier has daily limits, so heavy use can stop it for the day (limits reset at midnight Pacific time; your own limits are shown in Google AI Studio).
- **Free models only.** `FREE_MODELS` in `backend/config.py` lists the three models Google's pricing page shows as "Free of charge" (checked 26 Nov 2026): `gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.8-flash`. The backend refuses to start if `SMALL_MODEL`, `STRONG_MODEL` or `VALIDATOR_MODEL` is anything else, and `ask_text` / `ask_json` in `utils/llm_client.py` check the model again before every call. If Google retires a model, change it in `.env` (or the Render environment) and in `FREE_MODELS`.
- **Use a free key.** Create the key in Google AI Studio under a project that has no billing account linked. Google's pages only say that billing is switched on in AI Studio to leave the Free tier; the code cannot check this, so do not link a card to that project.
- **Free-tier data.** Google's pricing page says free-tier content may be used to improve its products. Scan public repositories only.

## The flow (same as Fig. 1 of the synopsis)

```
GitHub URL -> Fetcher -> Rule Checker -> Router + AI Review -> Validator -> Report
                                              ^                    |
                                              +--- retry if confidence < 70 (max 2 retries)
```

The whole flow is written in one place: `backend/pipeline.py`, function `scan_repo`.

## Folder map

```
reposcanner/
├── backend/
│   ├── main.py                  starts FastAPI, allows the frontend (CORS)
│   ├── config.py                all settings: model names, limits, confidence limit 70
│   ├── pipeline.py              runs the agents in order + the retry / confidence gate
│   ├── jobs.py                  runs a scan in the background, keeps its live log and result
│   ├── Dockerfile               how Render builds and starts the backend
│   ├── routes/
│   │   └── scan_routes.py       the REST APIs: POST /scan, GET /scan/{id}, POST /report/pdf
│   ├── agents/                  one file = one agent = one job
│   │   ├── fetcher_agent.py     clones the repo, reads files, counts lines and languages
│   │   ├── rule_checker_agent.py  runs the 3 checks below and gives the rule score
│   │   ├── router_agent.py      picks the small or the strong model
│   │   ├── review_agent.py      sends README + code to the chosen Gemini model
│   │   ├── validator_agent.py   second model checks the review, gives confidence
│   │   ├── detector_agent.py    estimates how much of the code an AI wrote
│   │   └── report_agent.py      combines scores, builds the final report and PDF
│   ├── checks/                  the "rules" used by the Rule Checker Agent
│   │   ├── secret_patterns.py   the regular expressions (API key, password...)
│   │   ├── secret_check.py      runs the regex line by line
│   │   ├── health_check.py      README / LICENSE / .gitignore / requirements
│   │   ├── quality_check.py     long files, long functions, comment percent
│   │   └── rule_score.py        the if-then point deductions (README missing = -10)
│   ├── utils/
│   │   ├── llm_client.py        the only file that talks to Gemini
│   │   ├── pdf_writer.py        builds the PDF with reportlab
│   │   └── numbers.py           keeps a number between 0 and 100
│   └── tests/test_scanner.py
├── render.yaml                  tells Render how to create the backend service
└── frontend/
    ├── app/page.js              the one page: holds report / log / error state
    ├── app/layout.js            fonts and html shell
    ├── app/globals.css          colours, paper texture, animations (Tailwind)
    ├── lib/api.js               the only file that calls the backend (fetch + polling)
    ├── lib/score.js             score ranges and their colours
    ├── lib/useCountUp.js        makes the big score count up
    └── components/
        ├── Hero, UrlForm, PipelineList       the top of the page
        ├── Progress                          live agent log while scanning
        ├── Report                            puts the result sections in order
        ├── Verdict, Gauge                    big score and the 0-100 ruler
        ├── RepoFacts, RuleFindings           sections 01 and 02
        │   └── Penalties, Secrets, Health, Quality
        ├── AiReview, Suggestions, AgentLog   sections 03, 04 and 05
        └── Section, SubHeading, LedgerRow, DownloadButton, ErrorNote, SiteHeader, SiteFooter
```

## "Where is this written?" (for the viva)

| Question | File | Function / name |
|---|---|---|
| Where does the request from the website arrive? | `backend/routes/scan_routes.py` | `start_scan` (`POST /scan`), `get_scan` (`GET /scan/{id}`) |
| Where does the frontend send the link? | `frontend/lib/api.js` | `runScan` |
| Where does the scan run in the background? | `backend/jobs.py` | `create_job`, `run_job` |
| Where are all agents called one after another? | `backend/pipeline.py` | `scan_repo` |
| Where is the GitHub link checked? (only github.com is allowed) | `backend/agents/fetcher_agent.py` | `GITHUB_URL`, `parse_github_url` |
| Where is the repo cloned? | `backend/agents/fetcher_agent.py` | `run` (`Repo.clone_from`, GitPython) |
| Where are files and lines counted? | `backend/agents/fetcher_agent.py` | `read_repo_files`, `count_languages` |
| Where is the regex for API keys / passwords? | `backend/checks/secret_patterns.py` | `SECRET_PATTERNS` |
| Where is the regex run on the code? | `backend/checks/secret_check.py` | `find_secrets` |
| Where is "README missing"? | `backend/checks/health_check.py` | `check_health` |
| Where is "very long function" found? | `backend/checks/quality_check.py` | `find_long_functions` (uses Python `ast`) |
| Where is "missing comments" found? | `backend/checks/quality_check.py` | `count_comments` |
| Where are the minus points (README = -10)? | `backend/checks/rule_score.py` | `MISSING_FILE_RULES`, `calculate_rule_score` |
| Where is the small / strong model chosen? | `backend/agents/router_agent.py` | `choose_model` |
| Where are the model names set? | `backend/config.py` and `backend/.env` | `SMALL_MODEL`, `STRONG_MODEL`, `VALIDATOR_MODEL` |
| Where is the prompt sent to Gemini? | `backend/agents/review_agent.py` | `review_code`, `summarise_readme` |
| Where is Gemini actually called? | `backend/utils/llm_client.py` | `ask_text`, `ask_json` |
| Where does Gemini get retried when it is busy? | `backend/utils/llm_client.py` | `generate` (3 tries per model), `ModelBusyError` |
| Where does it switch to another free model? | `backend/pipeline.py` | `call_with_fallback`, `model_order` |
| Where is the "how much AI-written code" guess made? | `backend/agents/detector_agent.py` | `run`, `pick_files`, `get_label` |
| Where is that guess added to the report? | `backend/pipeline.py` and `backend/agents/report_agent.py` | `run_ai_detection`, `build_report` |
| Where is it shown on the website? | `frontend/components/AiDetection.js` | |
| Where does the second model give confidence? | `backend/agents/validator_agent.py` | `run` |
| Where is the "confidence below 70" check? | `backend/pipeline.py` | `review_with_retries` (`if validation["confidence"] >= CONFIDENCE_LIMIT`) |
| Where is the limit 70 set? | `backend/config.py` | `CONFIDENCE_LIMIT` |
| What does a retry change? | `backend/pipeline.py` | `make_retry_plans` |
| Where is "not sure" decided? | `backend/pipeline.py` | `run_ai_review` (`"status": "sure" if is_sure else "not_sure"`) |
| Where is the final score calculated? | `backend/agents/report_agent.py` | `build_report` (average of rule score and AI score) |
| Where is the PDF made? | `backend/utils/pdf_writer.py` | `make_pdf` |
| Where is the Gemini key kept? | `backend/.env` (read in `backend/config.py`) | never sent to the frontend |
| Where does the live agent list come from while scanning? | `frontend/lib/api.js` (`runScan` asks every second) + `components/Progress.js` | `log` state in `app/page.js` |
| Where is the big score and the ruler drawn? | `frontend/components/Verdict.js`, `Gauge.js` | |

## How the model routing and retry work

1. **Router** (`router_agent.py`): README summary always goes to the small model. Code review goes to the strong model if the code is bigger than 500 lines or secrets were found, otherwise to the small model.
2. **Review**: the chosen model returns a JSON with score, summary, problems and tips.
3. **Validator**: a different model reads the review and the same code and gives a confidence from 0 to 100.
4. **Busy model:** if a Gemini model answers "busy" (503) or "limit" (429) three times in a row, the pipeline switches to another model from the free list and writes it in the agent log. The validator prefers a different model than the review; only if every other free model is busy does the review model check its own review, and the agent log says so. A 429 (limit reached) is not retried on the same model, other errors are retried up to 3 times, and every call has a 50 second deadline.
5. **Confidence gate** (limit 70):
   - Try 1: normal prompt, normal amount of code.
   - Try 2: stricter prompt and smaller code chunks.
   - Try 3: the strong model with the stricter prompt and smaller chunks.
   - Still below 70 after the 2 retries: the result is shown as **"not sure"** and the final score uses only the rule score.

## How the final score is calculated

- **Rule score** = 100 minus points: README missing -10, LICENSE / .gitignore / requirements missing -5 each, secrets -10 each (max -40), long files -2 each (max -10), long functions -1 each (max -10), under 5% comments -5.
- **AI score** = the score given by the review model (0 to 100).
- **Final score** = (rule score + AI score) / 2. If the AI result is "not sure" or skipped, final score = rule score.

## Possible viva questions

- **What is an agent here?** A small Python file with one function `run` that takes an input and gives an output to the next agent.
- **Why two models?** The small one is cheap for easy work, the strong one is better for big code. A different validator model checks the answer so we do not trust one model blindly.
- **Why is the key in `.env`?** So the Gemini key stays on the server and never reaches the browser. `.env` is in `.gitignore`.
- **Is the AI trained by us?** No. We only write prompts (see `review_agent.py`).
- **Which algorithms are used?** If-then rules (`rule_score.py`, `router_agent.py`), regular expressions (`secret_patterns.py`), LLM prompting, and confidence cross-checking (`validator_agent.py`).
- **Is the secret shown in the report?** No. Only the first 4 characters and `****` are shown (`hide_secret` in `secret_check.py`).
- **What if the repo is private or the link is wrong?** `fetcher_agent.run` catches the git error and the website shows a clear message.
- **Limits:** the long-function check works for Python files only; comment counting is a simple check on lines starting with `#`, `//`, `/*` or `*`; only files up to 200 KB are read.

## AI-written code estimate

- The AI Detector agent takes the 5 biggest code files (at least 15 lines each) and sends the first 3,000 characters of each to a small Gemini model.
- The model gives each file a number from 0 to 100 for how much it looks AI-written. The overall number is the average, weighted by the lines of each file.
- 70 and up is "Mostly AI-written", 30 to 69 is "Mixed", below 30 is "Mostly human-written".
- It does not change the final score. It is shown in its own section and in the PDF.
- It is only an estimate. No tool can prove who wrote code, and clean human code can look AI-written. If the models are busy the scan still finishes and the section says no estimate was made.
