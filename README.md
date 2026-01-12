# TechTrainingPro v3.0

> **A Modern Full-Stack Platform Powered by OpenAI GPT-4o**

![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)

## 🚀 Overview

TechTrainingPro is a complete modernization of a 2024 technical training project, rebuilt from the ground up with 2026's best practices. Originally a Python Tkinter desktop application, it's now a powerful full-stack web platform featuring:

- 🤖 **AI Chat** - Powered by OpenAI GPT-4o with multimodal capabilities
- 🛠️ **Smart DevOps Agent** - AI-powered AWS infrastructure management
- 🖼️ **Vision Lab** - Image analysis with GPT-4o Vision
- 📦 **Cloud Storage** - S3 file manager
- 📍 **Location Services** - Geolocation and geocoding

## 📊 Evolution Timeline

| Feature | v1.0 (2024) | v2.0 (2025) | v3.0 (2026) |
|---------|-------------|-------------|-------------|
| UI | Tkinter Desktop | Next.js 15 | Next.js 15 + React 19 |
| AI Model | Cohere (basic) | Gemini 2.0 | OpenAI GPT-4o |
| DevOps | Manual boto3 | AI-Powered Agent | Enhanced AI Agent |
| Vision | Vision API labels | Gemini Vision | GPT-4o Vision |
| Deployment | None | Docker | Docker + CI/CD ready |

## 🏗️ Architecture

```
TechTrainingPro-OpenAI/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── main.py         # Application entry
│   │   ├── config.py       # Environment config
│   │   ├── routers/        # API endpoints
│   │   └── services/       # Business logic (openai_service.py)
│   └── requirements.txt
├── frontend/                # Next.js 15 frontend
│   └── src/app/            # App Router pages
├── docker-compose.yml       # Container orchestration
└── .env.example            # Environment template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- OpenAI API key
- AWS credentials (optional, for cloud features)

### 1. Clone & Setup

```bash
cd TechTrainingPro-OpenAI

# Copy environment file
cp .env.example backend/.env

# Edit backend/.env and add your OpenAI API key
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the App

Visit [http://localhost:3000](http://localhost:3000) 🎉

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 🔑 Environment Variables

```env
# OpenAI API (required)
OPENAI_API_KEY=your_openai_api_key

# AWS (optional - for DevOps Agent & Storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1
```

## 📱 Features

### 🤖 AI Chat
- Powered by OpenAI GPT-4o
- Conversation memory
- Streaming responses
- Code assistance & debugging

### 🛠️ DevOps Agent
Natural language cloud management:
- "List my EC2 instances"
- "Launch a new t2.micro instance"
- "Show my S3 buckets"
- "What's my infrastructure status?"

### 🖼️ Vision Lab
- Image analysis & description
- OCR text extraction
- Object identification
- Custom analysis prompts

### 📦 Cloud Storage
- Browse S3 buckets
- Upload/download files
- Delete objects

### 📍 Location Services
- IP-based geolocation
- Location search
- Reverse geocoding
- Google Maps integration

## 👥 Team

**Original Project (2024)**
- Himanshu Kumar
- Mohd. Asif Ansari
- Saba Shamshad
- Ashutosh Singh
- Shikhar Pal

**Modernized (2026)**
- Rebuilt with modern stack & OpenAI GPT-4o

## 📄 License

MIT License - feel free to use and modify!

---

<p align="center">
  Built with ❤️ using Next.js, FastAPI & OpenAI GPT-4o
</p>
