# 📨 Emails Drafter — Automated Gmail Outreach Drafting Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg)](https://vitejs.dev/)
[![Gmail API](https://img.shields.io/badge/Gmail%20API-v1-EA4335.svg)](https://developers.google.com/gmail/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated, safety-first outreach pipeline built for internship applications and founder cold-contacting. It ingests company lead lists from Excel/CSV spreadsheets and generates perfectly personalized **Gmail drafts** directly inside your Gmail account on a human-like, staggered schedule.

---

> ⚠️ **CRITICAL SAFETY GUARANTEE**  
> **This system NEVER sends an email automatically.**  
> It strictly creates Gmail **Drafts** via the official Google OAuth API. You retain 100% human control: review each drafted message inside your Gmail inbox, verify attachments or personalized notes, and click **Send** yourself.

---

## 🌟 Key Features

- **📊 Flexible Spreadsheet Ingestion (`.xlsx` & `.csv`)**
  - Automatic column mapping with tolerant aliases (`Company`, `Founder / Contact Name`, `Email`, `Email Sent?`).
  - Duplicate detection and status validation (automatically skips already contacted leads).
- **🎯 Deterministic Templating Engine**
  - Strictly personalizes only `{{PERSON_NAME}}` and `{{COMPANY_NAME}}`.
  - Zero AI hallucinations, no erratic generative rewriting, and zero risk of altered claims.
- **⏱️ Intelligent Staggered Scheduler**
  - Powered by `APScheduler` with configurable start dates, daily sending windows, and minute intervals (e.g. 1 draft every 5–15 mins).
  - Enforces daily batch limits to avoid spam filters and respect Gmail API rate limits.
- **🔐 Official Gmail OAuth 2.0 Integration**
  - Uses the minimal required Google permission scope (`https://www.googleapis.com/auth/gmail.compose`).
  - No access to read your private emails; strictly limited to composing drafts.
- **💻 Modern Real-time Web Dashboard**
  - Built with **React 19**, **Vite**, and **Lucide Icons**.
  - Live metric counters (Total, Ready, Scheduled, Drafts Created, Failed, Skipped).
  - Interactive Contact Table with batch selector and status badges.
  - One-click modal preview to verify subject and rendered HTML/plain-text email before drafting.
  - Scheduler controls: **Start**, **Pause**, **Resume**, and **Stop**.
- **🛡️ Resilient & Crash-Proof**
  - Backed by an SQLite database tracking every contact's state.
  - Automatically resumes pending jobs and stuck queues upon server restart.
  - Automatic retry mechanism with exponential backoff on transient network failures.

---

## 🔄 System Architecture & Workflow

```mermaid
flowchart TD
    A[Excel / CSV File] -->|Upload & Validation| B[FastAPI Backend]
    B -->|Normalize & Store| C[(SQLite Database)]
    C -->|Fetch Pending Contacts| D[APScheduler Engine]
    D -->|Interval & Daily Limit Filter| E[Template Engine]
    E -->|Personalize {{NAME}} & {{COMPANY}}| F[Google Gmail API]
    F -->|Create Draft| G[Gmail Account Drafts Box]
    G -->|Human Review & Quality Check| H[Final Human Click to Send]
    
    I[React + Vite Dashboard] <-->|REST API & Real-time Status| B
```

---

## 📂 Project Structure

```text
emails-drafter/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── contacts.py        # Spreadsheet upload, contact listing, preview, retry
│   │   │   ├── gmail.py           # Google OAuth2 authorization, callback, status
│   │   │   ├── logs.py            # Execution and error logs
│   │   │   └── schedule.py        # Scheduler configuration and job control
│   │   ├── database.py            # SQLAlchemy SQLite engine & session management
│   │   ├── gmail_service.py       # Google API OAuth2 client & draft creation
│   │   ├── models.py              # Database models (Contact, ScheduleConfig, ActivityLog)
│   │   ├── scheduler.py           # APScheduler worker & rate limiting
│   │   ├── schemas.py             # Pydantic request/response schemas
│   │   ├── spreadsheet.py         # Pandas/openpyxl parser & column normalizer
│   │   └── template_engine.py     # Deterministic body & subject personalization
│   ├── main.py                    # FastAPI application entrypoint & CORS configuration
│   ├── requirements.txt           # Python backend dependencies
│   ├── .env.example               # Template environment configuration
│   └── uploads/                   # Staged upload directory
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main dashboard UI with stats, controls & contact tables
│   │   ├── App.css                # Component styling
│   │   ├── index.css              # Design system & dark theme tokens
│   │   └── main.jsx               # React DOM entrypoint
│   ├── index.html                 # HTML template
│   ├── package.json               # Frontend dependencies & scripts
│   └── vite.config.js             # Vite configuration
├── start.bat                      # 1-click Windows launcher for backend & frontend
├── .gitignore                     # Git ignore rules (protects credentials & uploads)
└── README.md                      # Project documentation
```

---

## 🛠️ Prerequisites

Before running the application, make sure you have:

- **Python 3.10+** installed
- **Node.js 18+** & **npm** installed
- A **Google Cloud Platform (GCP)** project with Gmail API enabled

---

## 🔑 Google Cloud OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `Email-Drafting-Agent`).
3. Navigate to **APIs & Services** > **Library** and search for **Gmail API**, then click **Enable**.
4. Go to **APIs & Services** > **OAuth consent screen**:
   - Choose **External** user type.
   - Enter an App name, User support email, and Developer contact information.
   - In **Scopes**, add `https://www.googleapis.com/auth/gmail.compose`.
   - In **Test users**, add your own Google email address.
5. Go to **APIs & Services** > **Credentials**:
   - Click **Create Credentials** > **OAuth client ID**.
   - Application type: **Web application**.
   - Under **Authorized redirect URIs**, add:
     ```text
     http://localhost:8000/api/gmail/callback
     ```
6. Copy your **Client ID** and **Client Secret**.

---

## 🚀 Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Matheletss/emails-drafter.git
cd emails-drafter
```

### 2. Configure Backend Environment

Copy `.env.example` to `backend/.env` and insert your Google Cloud credentials:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/gmail/callback
DATABASE_URL=sqlite:///./email_drafts.db
UPLOAD_DIR=./uploads
```

### 3. Setup Python Backend

```bash
# In backend directory:
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Setup Frontend

```bash
cd ../frontend
npm install
```

### 5. Running the Application

You can launch both frontend and backend concurrently:

#### Windows (1-Click Launch):
Double-click `start.bat` in the root folder, or run:
```bat
start.bat
```

#### Manual Launch:
- **Backend**:
  ```bash
  cd backend
  uvicorn main:app --reload --port 8000
  ```
  API will be available at `http://localhost:8000` (Docs: `http://localhost:8000/docs`).

- **Frontend**:
  ```bash
  cd frontend
  npm run dev
  ```
  Dashboard will be available at `http://localhost:5173`.

---

## 📑 Spreadsheet Format Specification

Upload any standard `.xlsx`, `.xls`, or `.csv` file. The parser automatically maps variations of column headers:

| Canonical Field | Recognized Headers | Required? | Example Value |
|---|---|:---:|---|
| **Company** | `Company`, `Company Name`, `Startup` | Yes | `LatentForce` |
| **Contact Name** | `Founder / Contact Name`, `Founder Name`, `Contact Name`, `Name` | Yes | `Nikhil` |
| **Email** | `Email`, `Email Address`, `Mail` | Yes | `founder@latentforce.ai` |
| **Email Sent?** | `Email Sent?`, `Email Sent`, `Status` | Optional | `Not Sent` *(Drafts created will be skipped if marked "Sent")* |

---

## 🧭 How to Use the Dashboard

1. **Connect Gmail**: Click the **Connect Gmail** button on the top right. You will be redirected to Google to authorize draft creation.
2. **Upload Leads**: Drag and drop your `.xlsx` or `.csv` spreadsheet into the upload area. The system will display the total valid contacts and batch ID.
3. **Configure Schedule**:
   - Set the Start Date and Start Time.
   - Set interval in minutes (e.g. `10` minutes between each draft).
   - Set Daily Cap (e.g. `20` drafts/day) and working hours (e.g. 09:00 to 18:00).
4. **Preview**: Click **Preview** on any contact row to inspect the generated subject line and body.
5. **Start Scheduling**: Click **Start Scheduler**. The backend will queue the drafts and create them safely in Gmail according to your schedule.
6. **Review in Gmail**: Open [Gmail](https://mail.google.com/), navigate to your **Drafts** folder, review each email, and send whenever ready!

---

## 📡 API Reference

Interactive documentation is available at `http://localhost:8000/docs`.

### Contacts (`/api/contacts`)
- `POST /api/contacts/upload` — Upload an Excel or CSV file.
- `GET /api/contacts/` — List contacts (filter by `batch_id` or `status`).
- `GET /api/contacts/batches` — Get summary stats of all uploaded batches.
- `GET /api/contacts/{id}/preview` — Preview rendered email for a specific lead.
- `POST /api/contacts/{id}/retry` — Reset a failed contact for re-processing.
- `GET /api/contacts/stats` — Aggregate status metrics.

### Scheduler (`/api/schedule`)
- `POST /api/schedule/config` — Save/update schedule configuration.
- `GET /api/schedule/config` — Retrieve current schedule settings.
- `POST /api/schedule/start` — Start scheduling for a batch (`live` or `preview` mode).
- `POST /api/schedule/pause` — Pause scheduler.
- `POST /api/schedule/resume` — Resume scheduler.
- `POST /api/schedule/stop` — Stop scheduler and clear pending jobs.
- `GET /api/schedule/status` — Get current scheduler state.

### Gmail Authentication (`/api/gmail`)
- `GET /api/gmail/auth-url` — Get Google OAuth 2.0 authorization URL.
- `GET /api/gmail/callback` — OAuth 2.0 callback endpoint.
- `GET /api/gmail/status` — Check authentication status & connected email.
- `POST /api/gmail/disconnect` — Revoke & remove saved credentials.

---

## 🛡️ Best Practices & Outreach Ethics

1. **Warm up your email**: Don't create 100 drafts on day 1 with a brand new email account.
2. **Keep intervals natural**: A setting of 8–15 minutes between emails mimics organic human activity.
3. **Verify validity**: Ensure emails in your spreadsheet are verified using tools like Hunter or NeverBounce to minimize bounce rates.
4. **Respect opt-outs**: Always honor any recipient asking to be removed from future outreach.

---

## 📄 License

This project is open-source and distributed under the [MIT License](LICENSE).
