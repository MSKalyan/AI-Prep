# AI Exam Preparation Platform

An AI-powered exam preparation platform for GATE and other competitive exams. Features smart roadmaps, adaptive mock tests, performance analytics, and AI-assisted learning.

## Features

- **Smart Roadmaps**: Generate personalized study plans based on exam syllabus
- **Mock Tests**: Create adaptive tests from PYQ database with AI fallback
- **Analytics**: Track performance, identify weak areas, get revision recommendations
- **AI Assistant**: Ask doubts and get explanations powered by Groq LLM

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django + DRF |
| Frontend | Next.js 16 + React 19 + TypeScript |
| Database | PostgreSQL |
| AI | Groq API |

## Project Structure

```
backend/
├── apps/
│   ├── users/          # Auth & profile
│   ├── roadmap/       # Study plans & PYQs
│   ├── mocktest/      # Test generation
│   ├── analytics/     # Performance tracking
│   └── ai_service/    # AI chat
└── config/

frontend/
├── src/
│   ├── app/           # Pages
│   ├── features/      # Feature modules
│   └── components/   # UI components
└── package.json
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

### Backend (.env)

```
DEBUG=True
SECRET_KEY=<secret>
DATABASE_URL=postgresql://user:pass@localhost:5432/db
GROQ_API_KEY=<key>
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## API Endpoints

- `POST /api/auth/register/` - Register
- `POST /api/auth/login/` - Login
- `POST /api/roadmap/generate/` - Generate roadmap
- `POST /api/mocktest/generate/` - Generate test
- `GET /api/analytics/` - Get analytics
- `POST /api/ai_service/chat/` - AI chat

## License

Educational use only.