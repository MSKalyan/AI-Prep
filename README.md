# AI-Based Exam Preparation Platform

## Overview

AI-Based Exam Preparation is a comprehensive full-stack learning platform designed to help students prepare efficiently for competitive exams like GATE through structured roadmaps, adaptive mock tests, detailed analytics, and AI-powered assistance.

The system combines:

*  Structured Syllabus Planning : Topic-based roadmaps with daily learning goals
*  Adaptive Mock Test Generation : LLM-powered question generation with fallback mechanisms
*  Performance Analytics : Topic-wise accuracy tracking and weak area detection
*  AI-Assisted Learning : Doubt resolution and personalized recommendations

 Tech Stack: 
*  Backend:  Django + Django REST Framework
*  Frontend:  Next.js (App Router) with TypeScript
*  Database:  PostgreSQL
*  Authentication:  JWT-based authentication
*  AI Integration:  Groq API for LLM-powered features

---

## Features

### Core Features

* 🔐  User Authentication : JWT-based secure login/registration
* 🗺️  AI-Generated Roadmaps : Personalized study plans based on exam type
* 📚  Topic Management : Hierarchical subject-topic structure
* 🧪  Mock Test System : Generate and attempt adaptive mock tests
* 📊  Performance Analytics : Comprehensive analytics dashboard with accuracy trends
* 🎯  Weak Topic Detection : Automatic identification of improvement areas
* 📈  Progress Tracking : Daily study sessions and completion monitoring
* 🤖  AI Question Generation : Fallback LLM-powered question creation when DB is insufficient
* 💬  AI Service Integration : Conversation-based doubt resolution

### AI-Oriented Capabilities

*  Adaptive Learning : Performance-based topic prioritization
*  LLM Fallback : Guaranteed test generation even with limited questions
*  Smart Analytics : Topic strength classification (weak/moderate/strong)
*  Revision Recommendations : Daily revision suggestions based on performance

---

## Project Structure

```
backend/
├── apps/
│   ├── users/           # User management and authentication
│   ├── roadmap/         # Study roadmap generation and management
│   ├── mocktest/        # Mock test generation and attempt tracking
│   ├── analytics/       # Performance analytics and metrics
│   ├── ai_service/      # AI conversation and assistance
│   └── config/          # Django settings and configuration
├── data/                # PYQ papers and syllabus data
├── manage.py
└── requirements.txt

frontend/
├── src/
│   ├── app/             # Next.js app router pages
│   │   ├── dashboard/   # Main dashboard with analytics
│   │   ├── auth/        # Authentication pages
│   │   └── api/         # API routes
│   ├── components/      # Reusable UI components
│   ├── features/        # Feature-specific modules
│   │   ├── auth/        # Authentication logic
│   │   ├── analytics/   # Analytics components and hooks
│   │   ├── roadmap/     # Roadmap management
│   │   └── mocktest/    # Mock test functionality
│   └── lib/             # Utilities and configurations
├── package.json
├── tailwind.config.js
└── playwright.config.ts  # E2E testing configuration
```

---

## Installation

### Prerequisites

* Python 3.11+
* Node.js 18+
* PostgreSQL 13+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Variables

Create `.env` file in backend root:

```env
DEBUG=True
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GROQ_API_KEY=your_groq_api_key
```

Create `.env.local` in frontend root:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## Development Workflow

### Running Services

```bash
# Terminal 1: Backend
cd backend && python manage.py runserver

# Terminal 2: Frontend
cd frontend && npm run dev



### Testing

```bash
# Backend tests
cd backend && python manage.py test

# Frontend tests
cd frontend && npm run test

# E2E tests
cd frontend && npx playwright test
```

---

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration

### Roadmap
- `GET /api/roadmap/` - Get user roadmaps
- `POST /api/roadmap/generate/` - Generate new roadmap
- `GET /api/roadmap/today/` - Get today's study plan

### Mock Tests
- `POST /api/mocktest/generate/` - Generate mock test
- `GET /api/mocktest/` - List user mock tests
- `POST /api/mocktest/{id}/submit/` - Submit test answers

### Analytics
- `GET /api/analytics/` - Comprehensive analytics
- `GET /api/analytics/performance/` - Topic performance data
- `GET /api/analytics/adaptive-study-plan/` - Adaptive study plan

### AI Service
- `POST /api/ai_service/chat/` - AI conversation
- `GET /api/ai_service/history/` - Chat history

---

## Database Models

### Core Models

-  User : Extended Django user with profile information
-  Exam : Exam types (GATE, etc.) with subjects
-  Subject : Subject categories under exams
-  Topic : Individual topics with weightage
-  Roadmap : User-specific study plans
-  RoadmapTopic : Topic assignments in roadmaps
-  Question : MCQ questions with metadata
-  MockTest : Generated test instances
-  TestAttempt : User test attempts with scores
-  Answer : Individual question responses
-  TopicPerformance : Analytics data per topic
-  PerformanceMetrics : Subject-level metrics

### Analytics Models

-  StudySession : Study time tracking
-  DailyProgress : Daily activity summary
-  WeakArea : Identified weak topics
-  PerformanceSnapshot : Historical performance data

---

## Key Features Implementation

### Mock Test Generation
- Fetches PYQ questions first
- Falls back to LLM generation if insufficient
- Guaranteed test creation with retry mechanisms
- Topic-based question selection

### Analytics System
- Real-time performance calculation
- Topic strength classification
- Weak area detection and prioritization
- Adaptive revision recommendations

### AI Integration
- Groq API for question generation
- Fallback mechanisms for reliability
- Topic-aware question creation

---

## Contributing

1. Create feature branch from `main`
2. Follow existing code patterns
3. Add tests for new features
4. Submit pull request with description

### Code Quality

- Use type hints in Python
- Follow TypeScript strict mode
- Write comprehensive tests
- Maintain code documentation

---

## Deployment

### Backend Deployment
```bash
# Production settings
DEBUG=False
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Frontend Deployment
```bash
npm run build
npm start
```

---

## Future Roadmap

*  Enhanced AI Features : Advanced RAG with vector databases
*  Mobile App : React Native companion app
*  Real-time Collaboration : Study groups and mentoring
*  Advanced Analytics : Predictive performance modeling
*  Integration APIs : Third-party exam platform connections

---

## Author

Mosalikanti Srinivasa Kalyan

---

## License

This project is for educational purposes. All rights reserved.
