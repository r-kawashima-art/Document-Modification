# Slack Integration Setup Guide

**Purpose**: Wire up the Document-Modification automation to Slack so that the full User Story flow runs end-to-end — data entry → approval → document generation → notification — without leaving Slack.

---

## 1. End-to-End Flow (User Story Recap)

```mermaid
sequenceDiagram
    actor HR as HR Staff
    actor Approver as Person in Charge
    participant SC as #input-channel (Slack)
    participant SA as #approval-channel (Slack)
    participant Bot as Slack Bot (Bolt App)
    participant Engine as doc_modifier (Python)
    participant GD as Google Drive

    HR->>SC: Posts personal info (Name, DOB, Passport No., …)
    SC->>Bot: Event: message posted
    Bot->>SA: Sends approval request Block Kit message
    Approver->>SA: Clicks ✅ Approve
    SA->>Bot: Interactive callback (action_id: approve)
    Bot->>Engine: Calls pipeline.run(template, data_row, formats=[docx,pdf])
    Engine-->>Bot: Returns output file paths
    Bot->>GD: Uploads docx + pdf via Google Drive API
    Bot->>SC: Posts "✅ Documents ready" with Drive links
```

---

## 2. Required Tools & Accounts

| Tool / Service | Purpose | Required Plan |
|---|---|---|
| **Slack workspace** | Channels, event routing, interactive components | Free or paid |
| **Slack App** (Bolt for Python) | Bot that receives events and sends messages | Free (Slack API) |
| **Python 3.10+** | Runtime for `doc_modifier` engine and Bolt app | — |
| **`slack_bolt`** Python package | Slack event handling & interactive component SDK | Free (PyPI) |
| **`slack_sdk`** Python package | Low-level API calls (file upload, etc.) | Free (PyPI) |
| **Google Drive API** (optional) | Upload rendered files to a shared Drive folder | Google Cloud free tier |
| **`google-api-python-client`** | Drive upload via service account | Free (PyPI) |
| **ngrok** (dev only) | Expose local Bolt app to Slack during development | Free tier |
| **A server / cloud host** (prod) | Run the Bolt app 24/7 | e.g. Cloud Run, EC2, Render |

---

## 3. Slack App Configuration

### 3.1 Create the App

1. Go to **[api.slack.com/apps](https://api.slack.com/apps)** → **Create New App** → **From scratch**.
2. Name it (e.g. `DocBot`) and select your workspace.

### 3.2 OAuth & Permissions (Bot Token Scopes)

Add these **Bot Token Scopes** under **OAuth & Permissions**:

| Scope | Why |
|---|---|
| `channels:history` | Read messages in public channels |
| `chat:write` | Post messages |
| `chat:write.public` | Post to channels the bot hasn't joined |
| `files:write` | Upload rendered documents |
| `im:write` | Send DMs for notifications |
| `users:read` | Resolve user display names |

Install the app to your workspace and copy the **Bot User OAuth Token** (`xoxb-…`).

### 3.3 Enable Event Subscriptions

Under **Event Subscriptions**:

- Toggle **Enable Events** on.
- Set **Request URL** to `https://<your-host>/slack/events`.
- Subscribe to **Bot Events**:
  - `message.channels` — fires when a message is posted in a channel the bot has joined.

### 3.4 Enable Interactivity

Under **Interactivity & Shortcuts**:

- Toggle **Interactivity** on.
- Set **Request URL** to `https://<your-host>/slack/events` (same endpoint; Bolt routes internally).

---

## 4. Environment Variables

Create a `.env` file at the project root (never commit this):

```dotenv
# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_SIGNING_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Channel IDs (copy from channel details in Slack)
INPUT_CHANNEL_ID=C0XXXXXXXXX       # channel where HR posts data
APPROVAL_CHANNEL_ID=C0YYYYYYYYY    # channel where approvers see requests

# Google Drive (optional)
GOOGLE_DRIVE_FOLDER_ID=1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_SERVICE_ACCOUNT_JSON=credentials/service_account.json

# Doc engine
TEMPLATE_PATH=templates/Template_Invitation_Letter_Adventure_India_tokenized.docx
OUTPUT_DIR=output/
```

---

## 5. Project Structure After Integration

```
Document-Modification/
├── src/
│   ├── doc_modifier/          # existing engine (unchanged)
│   └── slack_bot/
│       ├── __init__.py
│       ├── app.py             # Bolt app entry point
│       ├── handlers/
│       │   ├── message.py     # parses HR's data post → builds data row
│       │   ├── approval.py    # handles ✅/❌ button callbacks
│       │   └── drive.py       # uploads files to Google Drive
│       └── blocks.py          # Block Kit message builders
├── .env                       # secrets (gitignored)
├── credentials/
│   └── service_account.json   # Google service account (gitignored)
├── requirements.txt
└── ...
```

---

## 6. Installation

```bash
# 1. Install new dependencies
pip install slack-bolt slack-sdk python-dotenv google-api-python-client google-auth --break-system-packages

# 2. (Dev) Install ngrok and expose port 3000
ngrok http 3000
# Copy the https://xxxx.ngrok.io URL → paste into Slack App settings (§3.3 / §3.4)
```

---

## 7. Core Bot Code Skeleton

### `src/slack_bot/app.py`

```python
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

# Register handlers
from slack_bot.handlers.message import handle_data_post
from slack_bot.handlers.approval import handle_approve, handle_reject

app.message()(handle_data_post)
app.action("approve_doc")(handle_approve)
app.action("reject_doc")(handle_reject)

if __name__ == "__main__":
    app.start(port=3000)
```

### `src/slack_bot/handlers/message.py` (sketch)

```python
import re, os
from slack_bot.blocks import build_approval_block

FIELD_PATTERNS = {
    "name":                    r"Name[:\s]+(.+)",
    "date_of_birth":           r"DOB[:\s]+(.+)",
    "nationality":             r"Nationality[:\s]+(.+)",
    "passport_no":             r"Passport No[.:\s]+(.+)",
    "passport_issuing_country":r"Issuing Country[:\s]+(.+)",
    "date_of_issue":           r"Date of Issue[:\s]+(.+)",
    "date_of_expiry":          r"Date of Expiry[:\s]+(.+)",
    "mobile_no":               r"Mobile[:\s]+(.+)",
}

def handle_data_post(message, say, client):
    text = message.get("text", "")
    data_row = {}
    for token, pattern in FIELD_PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            data_row[token] = m.group(1).strip()

    if len(data_row) < 3:
        return  # not a data post; ignore

    # Store data_row temporarily (e.g. in-memory dict keyed by ts)
    PENDING[message["ts"]] = data_row

    client.chat_postMessage(
        channel=os.environ["APPROVAL_CHANNEL_ID"],
        blocks=build_approval_block(data_row, message["ts"]),
        text="Document approval request",
    )
```

### `src/slack_bot/handlers/approval.py` (sketch)

```python
import os
from doc_modifier.pipeline import run_pipeline
from slack_bot.handlers.drive import upload_to_drive

PENDING = {}  # ts → data_row (use Redis/DB in production)

def handle_approve(ack, body, client):
    ack()
    ts = body["actions"][0]["value"]
    data_row = PENDING.pop(ts, {})

    paths = run_pipeline(
        template=os.environ["TEMPLATE_PATH"],
        data_rows=[data_row],
        out_dir=os.environ["OUTPUT_DIR"],
        formats=["docx", "pdf"],
    )

    drive_links = [upload_to_drive(p) for p in paths]

    client.chat_postMessage(
        channel=os.environ["INPUT_CHANNEL_ID"],
        text=f"✅ Documents ready for *{data_row.get('name')}*:\n" +
             "\n".join(f"• <{link}|{link}>" for link in drive_links),
    )

def handle_reject(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=os.environ["INPUT_CHANNEL_ID"],
        text="❌ Document request was rejected. Please resubmit.",
    )
```

---

## 8. Google Drive Upload (optional)

```python
# src/slack_bot/handlers/drive.py
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def upload_to_drive(file_path: str) -> str:
    creds = Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"], scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body={
            "name": os.path.basename(file_path),
            "parents": [os.environ["GOOGLE_DRIVE_FOLDER_ID"]],
        },
        media_body=media,
        fields="webViewLink",
    ).execute()
    return file["webViewLink"]
```

To set up the service account:
1. Go to **Google Cloud Console** → **IAM & Admin** → **Service Accounts** → Create.
2. Download the JSON key → save to `credentials/service_account.json`.
3. Share the target Google Drive folder with the service account email (`…@….iam.gserviceaccount.com`) as **Editor**.

---

## 9. Data Entry Format for HR Staff

HR posts a message in the input channel using this format (the bot parses it with regex):

```
Name: Taro Yamada
DOB: 1990-04-15
Nationality: Japanese
Passport No.: TZ1234567
Issuing Country: Japan
Date of Issue: 2020-01-10
Date of Expiry: 2030-01-09
Mobile: +81-90-1234-5678
```

> **Tip**: Pin this format as a channel bookmark so HR always has it handy.

---

## 10. Production Deployment Checklist

- [ ] Deploy the Bolt app to a persistent host (Cloud Run, Heroku, EC2, etc.)
- [ ] Replace ngrok URL with the production URL in Slack App settings
- [ ] Move `PENDING` dict to Redis or a lightweight DB (SQLite / Cloud Firestore) so state survives restarts
- [ ] Store secrets in the host's secret manager (not `.env` files)
- [ ] Add error handling: notify HR channel if rendering fails
- [ ] Set up logging (structured JSON logs recommended)
- [ ] (Optional) Add a `/gendoc` slash command as an alternative entry point

---

## 11. Summary of What to Set Up

| Step | Action | Owner |
|---|---|---|
| 1 | Create Slack App at api.slack.com/apps | Dev |
| 2 | Add Bot Token Scopes listed in §3.2 | Dev |
| 3 | Enable Event Subscriptions + Interactivity (§3.3, §3.4) | Dev |
| 4 | Create `.env` with tokens and channel IDs | Dev |
| 5 | `pip install` new dependencies (§6) | Dev |
| 6 | Implement `src/slack_bot/` modules following §7 | Dev |
| 7 | (Optional) Create Google service account and share Drive folder (§8) | Dev / Admin |
| 8 | Test locally with ngrok; verify approval → render → notification | Dev |
| 9 | Deploy to production host; update Slack App URLs | Dev / Infra |
| 10 | Share data entry format (§9) with HR staff | Admin |
