# Plan: Gmail Internship Outreach Drafting Agent

## 1. Project Objective

Build a simple automation agent that takes an Excel/CSV spreadsheet containing startup/company contacts and creates personalized Gmail **drafts** on a configurable schedule.

### Critical rule

The system must **NEVER automatically send an email**.

The workflow is:

```text
Spreadsheet
    ↓
Validate contact
    ↓
Personalize fixed template
    ↓
Schedule
    ↓
Create Gmail Draft
    ↓
Human reviews
    ↓
Human manually clicks Send
```

The system is a drafting and scheduling tool, not an autonomous email sender.

---

## 2. Input Spreadsheet

The application must support:

- `.xlsx`
- `.csv`

Expected columns:

| Company | Founder / Contact Name | Email | Email Sent? |
|---|---|---|---|
| LatentForce | Nikhil | founder@latentforce.ai | Not Sent |
| MyFI | Kinnari | kinnari@askmyfi.com | Not Sent |
| FluxGen Technologies | Ganesh | ganesh@fluxgentech.com | Not Sent |

At minimum, these fields are required:

- `Company`
- `Founder / Contact Name`
- `Email`
- `Email Sent?`

The system should tolerate minor variations in column names where practical.

---

## 3. Personalization Rules

The email content is fixed.

Only these two values may change:

1. `{{PERSON_NAME}}` → recipient's name
2. `{{COMPANY_NAME}}` → company name

Everything else must remain exactly the same.

Example:

```text
Company = LatentForce
Founder / Contact Name = Nikhil
Email = nikhil@latentforce.ai
```

Generated email:

```text
Hello Nikhil,

...

I am writing this email for an internship at LatentForce for machine learning engineering or an Artificial Intelligence role.

...

I just want to learn as much as possible and contribute to the team at LatentForce.
```

Do not rewrite, improve, paraphrase, summarize, or otherwise modify the fixed email template.

---

## 4. Exact Email Template

Use this template exactly, with only the two substitutions described above.

```text
Hello {{PERSON_NAME}},

I hope you are doing well.

I am writing this email for an internship at {{COMPANY_NAME}} for machine learning engineering or an Artificial Intelligence role.

I am Sagar, a final-year engineering student from Birla Institute of Technology pursuing Mathematics and Computing.

I dont want to waste you time. So here is something about my work.

1. At The Linux Foundation, I worked on ML applications for telecom infrastructure and data anonymization, including autoencoder-based pipelines while evaluating privacy preservation and model performance
2. I co-founded Emplo AI, where I architected the product end-to-end across frontend, backend, database, and AI/ML, processing 2,000+ resumes and conducting 100+ AI interviews.
3. At Modal AI, I worked on multimodal video understanding using LaViLa and VideoRecap, processing 1,000+ video clips and reducing inference latency by ~50%.
4. Built DataWire, a multi-agent AI analytics platform using LangGraph and RAG, with specialized agents, real-time streaming, Redis caching, and external data integration.
5. Currently building Sponsa, a UPI-based tipping platform for YouTube Live streamers, working across React, FastAPI, MongoDB, Cashfree, WebSockets, and OBS.
6. I am familiar with PyTorch, TensorFlow/Keras, Scikit-Learn, NLP, RAG, LLMs, LangGraph, and building AI systems end-to-end.
7. I have published research on multi-objective optimization using NSGA-II, with the work provisionally accepted as a book chapter in Decision Analytics for Tourism Planning and Management.

I don't care about working hours and all, I just want to learn as much as possible and contribute to the team at {{COMPANY_NAME}}.

Here is resume:

https://drive.google.com/file/d/1Fs4htOssxanFrnsIUI6RSWCR633EhgkD/view?usp=sharing

Thanks & Regards
Sagar
```

---

## 5. Subject Line

Use:

```text
Machine Learning / AI Internship Opportunity at {{COMPANY_NAME}}
```

Only the company name is substituted.

---

## 6. Scheduling

The user must be able to configure a schedule before starting.

Example:

```text
Start date: October 10, 2026
Start time: 10:00 AM
Interval: 10 minutes
Daily limit: 20
```

The system then creates drafts sequentially:

```text
10:00 AM → Contact 1
10:10 AM → Contact 2
10:20 AM → Contact 3
10:30 AM → Contact 4
...
```

Scheduling configuration should support:

- Start date
- Start time
- Delay/interval between drafts
- Maximum number of drafts per day
- Optional daily start time
- Optional daily end time

If only a single start time is supplied, the first contact begins at that time and subsequent contacts follow the configured interval.

---

## 7. Gmail Integration

Use the Gmail API with OAuth 2.0.

Required flow:

1. Authenticate the user's Gmail account.
2. Read contacts from the spreadsheet.
3. Validate each contact.
4. Generate the personalized email.
5. Create a Gmail **Draft**.
6. Save the draft in Gmail.
7. Do not send the email.

The implementation must use Gmail's draft-creation functionality rather than the send functionality.

There must be no automatic send operation.

---

## 8. Spreadsheet Status Tracking

After a draft is successfully created, update the corresponding spreadsheet row.

Use statuses such as:

```text
Not Sent
Draft Created
Sent
Failed
Skipped
```

A successfully created draft must be marked:

```text
Draft Created
```

It must **not** be marked `Sent`, because the application did not send the email.

If the user manually sends it later, they can update the status to:

```text
Sent
```

---

## 9. Duplicate Protection

Prevent accidental duplicate drafts.

Before processing a contact:

- Check the spreadsheet status.
- Check the contact email.
- Check the application's processing/state database.
- Where possible, retain the Gmail Draft ID.

If:

```text
Email Sent? = Draft Created
```

then skip the contact by default.

Maintain a unique identifier based on the recipient email address.

If the same email address has already been processed by the system, do not create another draft unless the user explicitly retries it.

---

## 10. Validation

Before creating a draft, validate:

- Email address exists.
- Email address has valid syntax.
- Company name exists.
- Contact name exists.
- Contact has not already been processed.

If a required field is missing, mark the row:

```text
Failed
```

and record the reason.

Example:

```text
Failed — Missing contact name
```

One invalid row must not stop the rest of the batch.

---

## 11. Dashboard / User Interface

Build a simple interface.

### Upload

```text
[ Upload Excel / CSV ]
```

After upload, show:

```text
Total Contacts: 50
Valid Contacts: 47
Already Processed: 3
Ready to Process: 44
```

### Schedule configuration

```text
Start Date:  [________]
Start Time:  [________]
Interval:    [10 minutes]
Daily Limit: [20]
```

### Preview

Allow the user to select a contact and preview exactly what will become the Gmail draft:

```text
To: founder@example.com
Subject: Machine Learning / AI Internship Opportunity at Example Company

Hello Rahul,

...
```

The preview must use the exact fixed template.

### Controls

Provide:

- Start Automation
- Pause
- Resume
- Stop
- Preview
- View Logs

---

## 12. Human Approval / Safety

This is mandatory.

The application must not have an automatic email sending workflow.

Required:

```text
Spreadsheet
    ↓
Generate personalized content
    ↓
Schedule
    ↓
Create Gmail Draft
    ↓
Human reviews
    ↓
Human manually clicks Send
```

Never implement:

```text
Spreadsheet
    ↓
Generate email
    ↓
Automatically Send
```

The system should make it obvious in the UI that drafts are created and sending remains a manual action.

---

## 13. Error Handling

If Gmail API fails:

```text
Status = Failed
Error = Gmail API error
```

Temporary failures should use retry logic with exponential backoff.

Retries must be idempotent so that a retry does not accidentally create duplicate drafts.

The scheduler should be resumable after:

- Application crash
- Computer restart
- Temporary network failure
- Gmail API failure

The system should resume from the last confirmed successful operation.

---

## 14. Logging

Maintain an activity log with:

```text
Timestamp
Company
Contact Name
Email
Scheduled Time
Status
Gmail Draft ID
Error
```

Example:

```text
10 Oct 2026 10:00 | LatentForce | Nikhil | nikhil@... | Draft Created
10 Oct 2026 10:10 | MyFI | Kinnari | kinnari@... | Draft Created
10 Oct 2026 10:20 | FluxGen | Ganesh | ganesh@... | Failed
```

The dashboard should allow the user to inspect these logs.

---

## 15. Recommended Architecture

Keep the architecture modular and simple.

```text
Frontend / Dashboard
        ↓
Spreadsheet Parser
        ↓
Contact Validator
        ↓
Email Template Engine
        ↓
Scheduler
        ↓
Gmail OAuth/API Service
        ↓
Draft Creation
        ↓
Database / State Store
```

Recommended technology:

- Python
- FastAPI backend
- React / Next.js frontend if a web UI is required
- Pandas / OpenPyXL for spreadsheet processing
- Gmail API
- OAuth 2.0
- SQLite initially for state and logging
- APScheduler or equivalent scheduling library

Avoid unnecessary infrastructure for the MVP.

---

## 16. State Management

The application should maintain persistent state so that restarting the application does not lose progress.

Suggested contact state:

```text
email
company
contact_name
status
scheduled_time
processed_at
gmail_draft_id
attempt_count
error
```

Suggested statuses:

```text
NOT_SENT
SCHEDULED
PROCESSING
DRAFT_CREATED
FAILED
SKIPPED
SENT
```

`SENT` is informational/manual and must never be set merely because a draft was created.

---

## 17. OAuth and Security

Use Gmail OAuth 2.0.

Never ask for or store the user's Gmail password.

Store sensitive credentials securely, preferably through:

```text
Environment variables
```

or an appropriate local secrets mechanism.

Do not commit:

- OAuth client secrets
- Access tokens
- Refresh tokens
- API keys
- `.env` files containing secrets

to Git.

Use the minimum Gmail permissions/scopes required for creating drafts.

---

## 18. Scheduling Logic

A possible scheduling algorithm:

```text
1. Load spreadsheet.
2. Normalize column names.
3. Validate rows.
4. Filter already processed contacts.
5. Sort remaining contacts in spreadsheet order.
6. Calculate scheduled time for each contact.
7. Persist scheduled jobs.
8. At each scheduled time:
      a. Re-check contact state.
      b. Validate again.
      c. Generate subject.
      d. Generate email body.
      e. Create Gmail draft.
      f. Persist Gmail Draft ID.
      g. Update spreadsheet status to Draft Created.
      h. Write activity log.
9. Continue until batch is complete.
```

If the application restarts:

```text
Load persisted jobs
    ↓
Identify completed jobs
    ↓
Identify pending jobs
    ↓
Resume pending jobs
```

Do not blindly recreate completed drafts.

---

## 19. Spreadsheet Handling

The original spreadsheet should not be destroyed or overwritten unexpectedly.

Prefer:

- Loading the uploaded spreadsheet.
- Keeping a backup/original copy.
- Updating statuses in a controlled way.
- Allowing the user to download the updated spreadsheet.

If a database is used for application state, the spreadsheet remains the human-readable contact source while the database handles reliable processing state.

---

## 20. Preview and Testing Mode

Before running real Gmail operations, provide a dry-run/test mode.

Example:

```text
Mode:
( ) Test / Preview
( ) Create Gmail Drafts
```

In preview mode:

- Do not call Gmail draft creation.
- Show generated recipients.
- Show subjects.
- Show personalized bodies.
- Show scheduled times.

This allows the user to verify personalization before creating drafts.

---

## 21. MVP Development Phases

### Phase 1 — Project Setup

- Set up backend.
- Set up frontend if needed.
- Create environment configuration.
- Create SQLite database.
- Establish project structure.

### Phase 2 — Spreadsheet Import

- Upload XLSX/CSV.
- Parse spreadsheet.
- Normalize columns.
- Validate rows.
- Display contact statistics.

### Phase 3 — Template Engine

Implement exactly two variables:

```text
{{PERSON_NAME}}
{{COMPANY_NAME}}
```

Generate:

- Subject
- Body

Add automated tests proving that no other text changes.

### Phase 4 — Preview

Build contact preview.

Verify:

- Recipient
- Subject
- Name substitution
- Company substitution
- Exact fixed body

### Phase 5 — Gmail OAuth

Implement:

- Google OAuth flow
- Secure token handling
- Gmail connection test

### Phase 6 — Gmail Draft Creation

Implement Gmail draft creation only.

Test that:

- Draft appears in Gmail.
- Recipient is correct.
- Subject is correct.
- Body is correct.
- No email is sent.

### Phase 7 — Scheduler

Implement:

- Start time
- Interval
- Daily limit
- Pause
- Resume
- Stop
- Persistent scheduled jobs

### Phase 8 — State and Duplicate Protection

Implement:

- Contact state
- Draft IDs
- Idempotency
- Retry handling
- Resume after restart

### Phase 9 — Logging and Status Updates

Implement:

- Activity log
- Spreadsheet status updates
- Error tracking
- Failed contact handling

### Phase 10 — End-to-End Testing

Test:

- 1 contact
- Multiple contacts
- Missing name
- Missing company
- Invalid email
- Duplicate email
- Already processed contact
- Gmail API failure
- Application restart
- Scheduler pause/resume
- Draft creation
- Confirmation that no email is automatically sent

---

## 22. Acceptance Criteria

The MVP is complete only when all of the following work:

### Spreadsheet

- [ ] Upload XLSX.
- [ ] Upload CSV.
- [ ] Detect required columns.
- [ ] Validate contacts.
- [ ] Display contact statistics.

### Personalization

- [ ] Correct person name.
- [ ] Correct company name.
- [ ] No unintended content changes.
- [ ] Correct subject line.
- [ ] Correct resume link.

### Gmail

- [ ] OAuth works.
- [ ] Gmail Draft is created.
- [ ] Recipient is correct.
- [ ] Subject is correct.
- [ ] Body is correct.
- [ ] Email is NOT sent automatically.

### Scheduling

- [ ] Configurable start time.
- [ ] Configurable interval.
- [ ] Daily limit.
- [ ] Pause.
- [ ] Resume.
- [ ] Stop.
- [ ] Persistent scheduling state.

### Reliability

- [ ] Duplicate protection.
- [ ] Retry handling.
- [ ] Crash recovery.
- [ ] Error logging.
- [ ] Gmail Draft ID stored.

### UX

- [ ] Preview.
- [ ] Clear status.
- [ ] Activity log.
- [ ] Easy start/pause/resume controls.

---

## 23. Example End-to-End Run

Input:

```text
Company: LatentForce
Contact: Nikhil
Email: nikhil@latentforce.ai
Status: Not Sent
```

Configuration:

```text
Start: 10:00 AM
Interval: 10 minutes
```

At 10:00 AM:

```text
To:
nikhil@latentforce.ai

Subject:
Machine Learning / AI Internship Opportunity at LatentForce
```

Body begins:

```text
Hello Nikhil,

I hope you are doing well.

I am writing this email for an internship at LatentForce for machine learning engineering or an Artificial Intelligence role.
```

The application creates the Gmail draft.

Spreadsheet:

```text
Email Sent? = Draft Created
```

Log:

```text
10:00 AM | LatentForce | Nikhil | nikhil@latentforce.ai | Draft Created | <draft-id>
```

The user then opens Gmail, reviews the draft, and manually clicks **Send**.

---

## 24. Future Enhancements — Not Required for MVP

Do not implement these until the MVP works reliably:

- Multiple email templates
- AI-generated personalization
- Automatic follow-up drafts
- Reply tracking
- Gmail inbox synchronization
- Analytics dashboard
- Contact enrichment
- CRM integration
- Multiple Gmail accounts
- Cloud deployment
- Team accounts
- Advanced campaign management

The MVP should remain focused on:

**Spreadsheet → Personalize fixed template → Schedule → Create Gmail Draft → Human manually sends.**

---

## 25. Final Product Definition

The final MVP is a controlled internship outreach assistant.

Its sole automated action is:

> **Create the correct personalized Gmail draft at the scheduled time.**

It must never independently send an email.

The user retains final control over every outgoing message.
