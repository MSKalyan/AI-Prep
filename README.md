# AI-Based Exam Preparation Platform

A full-stack AI-powered exam preparation platform for competitive exams like GATE. Features adaptive mock tests, study roadmaps, performance analytics, and AI-assisted learning.

## Tech Stack

- **Backend**: Django + Django REST Framework
- **Frontend**: Next.js 16 (App Router) + TypeScript + React 19
- **Database**: PostgreSQL
- **AI**: Groq API for LLM-powered features

## Features

- User Authentication (JWT)
- Study Roadmap Generation
- Adaptive Mock Test System
- Performance Analytics & Weak Area Detection
- AI-Powered Doubt Resolution
- Topic-wise Progress Tracking

## Project Structure

```
├── backend/              # Django REST API
│   ├── apps/
│   │   ├── users/       # Authentication
│   │   ├── roadmap/    # Study plans
│   │   ├── mocktest/    # Test system
│   │   ├── analytics/   # Performance tracking
│   │   └── ai_service/ # AI assistant
│   └── config/
│
└── frontend/            # Next.js application
    ├── src/
    │   ├── app/        # Pages (dashboard, auth, etc.)
    │   ├── features/   # Feature modules
    │   │   ├── auth/
    │   │   ├── analytics/
    │   │   ├── roadmap/
    │   │   ├── mocktest/
    │   │   ├── ai/
    │   │   └── study/
    │   └── components/
    └── package.json
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GROQ_API_KEY=your_groq_api_key
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/auth/` | Authentication |
| `/api/roadmap/` | Study roadmaps |
| `/api/mocktest/` | Mock tests |
| `/api/analytics/` | Performance data |
| `/api/ai_service/` | AI chat |

## License

Educational use only. All rights reserved.