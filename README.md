# AI-Based Exam Preparation Platform

## Overview

AI-Based Exam Preparation is a full-stack learning platform designed to help students prepare efficiently for competitive exams using structured roadmaps, adaptive mock tests, analytics, and AI-powered assistance.

The system combines:

* Structured syllabus planning
* Personalized learning roadmaps
* Mock testing and performance analytics
* AI-assisted doubt resolution and adaptive recommendations

Architecture is built using:

* **Backend:** Django + Django REST Framework
* **Frontend:** Next.js (App Router)
* **Database:** PostgreSQL
* **Async Processing:** Celery
* **Authentication:** JWT-based authentication

---

## Features

### Core Features

* User authentication and profile management
* AI-generated study roadmaps
* Topic-wise structured preparation
* Mock test generation and tracking
* Performance analytics and weak area detection
* Daily progress tracking
* Study session tracking
* Adaptive learning support

### AI-Oriented Capabilities

* Roadmap generation jobs with async tracking
* RAG-ready document structure (future integration)
* Analytics-driven improvement suggestions

---

## Project Structure

```
backend/
  apps/
    users/
    roadmap/
    mocktest/
    analytics/
    ai_service/
  config/

frontend/
  src/
    app/
    components/
    features/
```

---

## Installation

### Requirements

* Python 3.11+
* Node.js 18+
* PostgreSQL
* Redis (for Celery)

---

### Backend Setup

```
cd backend

python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

---

### Frontend Setup

```
cd frontend

npm install
npm run dev
```

---

## Environment Variables

Create `.env` file in backend root.

Example:

```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

Do NOT commit `.env` files.

---

## Development Workflow

This project follows sprint-based development.

### Sprint 1 — Project Setup & Authentication

* Django project structure
* PostgreSQL configuration
* JWT authentication
* Next.js setup
* Backend–frontend API integration

### Sprint 2 — Core Data Models & APIs

* Exam and roadmap models
* Topic structure
* Mock test system
* Performance analytics models
* CRUD API development

---

## Git Workflow

* Work is done using feature branches.
* Each sprint is pushed to a separate branch.
* Merge Requests are created for review by team lead.

Example:

```
feature/sprint-1
feature/sprint-2
```

---

## Usage

1. Register/Login using authentication system.
2. Select target exam.
3. Generate study roadmap.
4. Track progress and complete topics.
5. Take mock tests.
6. Analyze performance metrics and weak areas.

---

## Future Roadmap

* AI-driven adaptive learning recommendations
* Vector database integration for RAG
* Advanced analytics dashboard
* ISR/SSR optimization for frontend
* Automated test generation

---

## Contributing

Development is team-based. Follow guidelines:

* Create new feature branch.
* Write clean commits.
* Avoid committing secrets or cache files.
* Submit Merge Request for review.

---

## Author

Mosalikanti Srinivasa Kalyan

---

## Project Status

Active development — sprint-based implementation in progress.
