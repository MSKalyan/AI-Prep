# AI Exam Preparation Platform - Backend

A full-stack AI-powered exam preparation platform with Django REST Framework backend, implementing RAG (Retrieval-Augmented Generation) architecture for intelligent doubt clearing and question generation.

## 🚀 Features

-  User Authentication : Token-based authentication with custom user model
-  AI-Powered Roadmap Generation : Personalized study plans using LLM
-  Mock Tests : Create and take practice tests with auto-grading
-  RAG-based AI Tutor : Ask questions and get context-aware answers
-  Analytics Dashboard : Track performance, identify weak areas, study streaks
-  RESTful API : Clean, well-documented API endpoints

## 🏗️ Architecture

### Tech Stack
-  Framework : Django 6.0 + Django REST Framework
-  Database : PostgreSQL
-  AI/ML : Groq API for LLM-powered features
-  Authentication : JWT-based authentication

### Apps Structure

```
backend/
├── apps/
│   ├── users/          # User management & authentication
│   ├── roadmap/        # Study roadmap generation
│   ├── mocktest/       # Question bank & mock tests
│   ├── ai_service/     # AI assistance implementation
│   └── analytics/      # Performance tracking
├── config/             # Project settings & URLs
└── manage.py
```

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Groq API key (for AI features)

## 🔧 Installation

### 1. Clone and Setup Environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env` and update:
- `SECRET_KEY`: Generate a secure key
- `DB_*`: PostgreSQL credentials
- `OPENAI_API_KEY`: Your OpenAI API key
- Other settings as needed

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb ai_exam_prep

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

## 🚀 Running the Application

### Backend Server

```bash
python manage.py runserver
```

API will be available at: `http://localhost:8000`

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PATCH /api/auth/profile/` - Update profile

### Roadmap
- `POST /api/roadmap/` - Generate personalized roadmap
- `GET /api/roadmaps/` - List user's roadmaps
- `GET /api/roadmap/<id>/` - Get roadmap details
- `PATCH /api/roadmap/<id>/` - Update roadmap / mark topics complete

### Mock Tests
- `GET /api/questions/` - List questions (with filters)
- `POST /api/mocktest/` - Create mock test
- `GET /api/mocktest/<id>/` - Get test details
- `POST /api/submit-answer/` - Submit answer
- `POST /api/results/` - Finalize test and get results
- `GET /api/results/` - Get past results

### AI Service
- `POST /api/ask-ai/` - Ask AI a question (RAG-powered)
- `POST /api/generate-questions/` - Generate questions using AI
- `POST /api/generate-practice/` - Generate practice set

### Analytics
- `GET /api/analytics/` - Comprehensive user analytics
- `GET /api/analytics/stats/` - Detailed performance stats

## 🎯 Key Features Implementation

### RAG Architecture

The AI service implements Retrieval-Augmented Generation:

1.  Retrieval : Fetch relevant documents from knowledge base
2.  Augmentation : Build context from retrieved documents
3.  Generation : Use LLM with context to generate answers

```python
# Example usage in services.py
relevant_docs = RAGService.retrieve_relevant_documents(query)
context = RAGService.build_context(relevant_docs)
answer = AIService.ask_ai(question, context)
```

### Service Layer Pattern

All business logic is in service layers, not views:

```python
# Example: RoadmapService, MockTestService, AIService, AnalyticsService
roadmap = RoadmapService.generate_roadmap(user, exam_name, ...)
```


## 📦 Database Models

### Key Models:
-  User : Custom user with exam preparation fields
-  Roadmap & RoadmapTopic : Study plan structure
-  Question, MockTest, TestAttempt, Answer : Testing system
-  Document, Conversation, Message : AI/RAG system
-  PerformanceMetrics, WeakArea, DailyProgress : Analytics

## 🔐 Security

- Token-based authentication
- CORS configured for frontend
- Environment variables for sensitive data
- SQL injection protection (Django ORM)
- Password hashing (Django default)

## 🚀 Deployment Notes

### Production Checklist:
1. Set `DEBUG=False`
2. Update `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Set up proper database (PostgreSQL)
5. Use gunicorn/uwsgi for WSGI
6. Set up reverse proxy (nginx)
7. Configure HTTPS
8. Set up monitoring (Sentry)

### Environment Variables:
All sensitive configuration is in environment variables - never commit `.env` file!
