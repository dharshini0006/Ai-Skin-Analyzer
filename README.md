# 🧴 AI Skin Health Analyzer

An AI-powered skin health analyzer that uses **Groq Vision (LLaMA 4)** to analyze your selfie and generate a personalized skincare report — completely free.

## ✨ Features

- 📸 Upload a selfie → get instant skin analysis
- 🔍 Detects acne, dark spots, redness, tanning, oiliness
- 💯 Overall skin health score (0–100)
- 🧬 Estimates biological skin age
- 🌅 Personalized morning & night skincare routine
- ☀️ Live UV index, AQI, humidity data (Chennai)
- 📊 Beautiful real-time dashboard

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Backend | Python, FastAPI |
| AI Vision | Groq API — LLaMA 4 Scout (free) |
| Weather | Open-Meteo API (no key needed) |

## 📁 Project Structure

```
AI-Skin-Analyzer/
├── frontend/
│   └── ai_skin_health_analyzer.html
├── backend/
│   ├── main.py
│   └── requirements.txt
├── uploads/          # user images saved here (gitignored)
└── README.md
```

## 🚀 Getting Started

### 1. Get a free Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Sign up → API Keys → Create API Key
- Copy the key (starts with `gsk_...`)

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY="gsk_your_key_here"
uvicorn main:app --reload --port 8000
```

### 3. Serve the frontend

```bash
cd frontend
python -m http.server 5500
```

### 4. Open in browser

```
http://localhost:5500/ai_skin_health_analyzer.html
```

## ⚠️ Important

- **Never commit your API key** — always use `export GROQ_API_KEY=...` in terminal
- The `uploads/` folder is gitignored — user photos are never committed
- This is for informational purposes only, not a substitute for professional medical advice

## 📸 Demo

Upload any selfie → the AI analyzes skin condition → dashboard shows:
- Skin score, type, and grade
- Concern breakdown with severity bars
- Live environmental risk factors
- Full AM/PM skincare routine
- Prioritized recommendations
