# ResearchAI — AI-Powered Research Agent

> Built with **Python Flask** + **IBM Granite** on **watsonx.ai**

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![IBM watsonx](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

---

## Features

| Capability | Description |
|---|---|
| 🔍 **Paper Search** | Live arXiv search with abstracts and links |
| 📄 **Summarisation** | AI summaries of papers and uploaded PDFs |
| 📚 **Citations** | APA, IEEE, MLA auto-generation |
| 💡 **Research Gaps** | Identify gaps and generate hypotheses |
| 📊 **Reports** | Full structured academic reports |
| 📎 **PDF Upload** | Upload and analyse your own PDFs |
| 💬 **AI Chat** | Conversational research assistant |
| 🌙 **Dark Mode** | Responsive dark/light UI |

---

## Project Structure

```
research-agent/
├── app.py                    # Flask application & routes
├── models.py                 # SQLAlchemy database models
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── agent/
│   ├── __init__.py
│   ├── instructions.py       # AGENT_INSTRUCTIONS config
│   ├── watsonx_client.py     # IBM Granite API client
│   └── research_tools.py    # Research tools (search, cite, report…)
├── templates/
│   ├── base.html             # Base layout
│   ├── index.html            # Home page
│   └── chat.html             # Chat interface
└── static/
    ├── css/style.css         # Dark-mode styles
    ├── js/app.js             # Global utilities
    ├── js/chat.js            # Chat interface logic
    └── uploads/              # PDF upload storage
```

---

## Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/yourname/research-agent.git
cd research-agent
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```
### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your IBM Cloud credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
FLASK_SECRET_KEY=your-random-secret-key
```

### 3. Run

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Getting IBM Cloud Credentials (Free Lite Tier)

### Step 1 — Create IBM Cloud Account
1. Go to [https://cloud.ibm.com/registration](https://cloud.ibm.com/registration)
2. Sign up for a **free Lite account** (no credit card required)

### Step 2 — Create an API Key
1. Go to **Manage → IAM → API Keys**
   [https://cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)
2. Click **Create an IBM Cloud API key**
3. Name it `watsonx-research-agent` → **Create**
4. **Copy the key immediately** (shown only once)
5. Paste into `.env` as `IBM_API_KEY`

### Step 3 — Create a watsonx.ai Project
1. Go to [https://dataplatform.cloud.ibm.com/wx/home](https://dataplatform.cloud.ibm.com/wx/home)
2. Click **New project → Create an empty project**
3. Name it `ResearchAI`
4. Open the project → **Manage tab → General**
5. Copy the **Project ID** → paste as `WATSONX_PROJECT_ID`

### Step 4 — Associate Watson Machine Learning Service
1. Inside your project → **Manage → Services & integrations**
2. Click **Associate service**
3. Choose **Watson Machine Learning** → select **Lite plan** (free)
4. Click **Associate**

### Step 5 — Verify the Model ID
Available IBM Granite models on Lite tier:
- `ibm/granite-3-8b-instruct` ✅ (recommended — free tier)
- `ibm/granite-13b-instruct-v2`

Set in `.env`:
```env
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

---

## Customising the Agent

Edit [`agent/instructions.py`](agent/instructions.py) to change agent behaviour:

```python
AGENT_INSTRUCTIONS = {
    "research_domain": "computer science",   # Focus domain
    "tone": "professional and concise",       # Response tone
    "default_citation_style": "APA",          # APA | IEEE | MLA
    "research_depth": "standard",             # quick | standard | deep
    "system_prompt": "You are ...",           # Full system prompt
    "safety_rules": [...],                    # Safety guardrails
}
```

Or set via `.env`:
```env
RESEARCH_DOMAIN=medicine
DEFAULT_CITATION_STYLE=IEEE
RESEARCH_DEPTH=deep
```

---

## Deploying to IBM Cloud (Code Engine — Lite)

### Prerequisites
- IBM Cloud CLI: [https://cloud.ibm.com/docs/cli](https://cloud.ibm.com/docs/cli)
- Code Engine plugin: `ibmcloud plugin install code-engine`

### Deploy Steps

```bash
# 1. Login
ibmcloud login --apikey $IBM_API_KEY -r us-south

# 2. Target resource group
ibmcloud target -g Default

# 3. Create / select Code Engine project
ibmcloud ce project create --name research-agent-project
ibmcloud ce project select --name research-agent-project

# 4. Create secrets from .env
ibmcloud ce secret create --name ra-secrets \
  --from-literal IBM_API_KEY=$IBM_API_KEY \
  --from-literal WATSONX_PROJECT_ID=$WATSONX_PROJECT_ID \
  --from-literal FLASK_SECRET_KEY=$FLASK_SECRET_KEY

# 5. Deploy application (from GitHub or local image)
ibmcloud ce app create \
  --name research-agent \
  --image icr.io/your-namespace/research-agent:latest \
  --env-from-secret ra-secrets \
  --env WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env GRANITE_MODEL_ID=ibm/granite-3-8b-instruct \
  --min-scale 0 \
  --max-scale 2 \
  --port 5000

# 6. Get URL
ibmcloud ce app get --name research-agent --output url
```

### Dockerfile (for container deployment)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

---

## IBM Cloud Lite Tier Limits

| Resource | Lite Limit |
|---|---|
| Watson Machine Learning | 20 RU/month |
| Code Engine | 100K vCPU-seconds/month |
| IBM Cloud Object Storage | 25 GB storage |
| API calls | ~500 Granite calls/month on free tier |

> **Tip:** Use `ibm/granite-3-8b-instruct` — it's the most token-efficient model on the Lite tier.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `IBM_API_KEY` | ✅ | — | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | ✅ | — | watsonx.ai project ID |
| `WATSONX_URL` | ✅ | us-south | watsonx.ai endpoint URL |
| `GRANITE_MODEL_ID` | ✅ | granite-3-8b-instruct | IBM Granite model to use |
| `FLASK_SECRET_KEY` | ✅ | — | Flask session secret |
| `DEFAULT_CITATION_STYLE` | ❌ | APA | APA / IEEE / MLA |
| `RESEARCH_DEPTH` | ❌ | standard | quick / standard / deep |
| `RESEARCH_DOMAIN` | ❌ | (general) | e.g., "medicine" |
| `ENABLE_ARXIV_SEARCH` | ❌ | true | Enable live arXiv search |

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built with ❤️ using IBM Granite on watsonx.ai*
