# 🎓 Flokus Academy — Master Homeschooling LMS & Operating System

**Flokus Academy** is a comprehensive, gamified Learning Management System (LMS) and homeschooling dashboard built for 5th-grade instruction. It synchronizes a 9-program curriculum suite into a single interface, balancing core academic hubs, applied STEM spokes, XP gamification, AI Socratic tutoring, and parental compliance tracking.

> **Note**: Flokus Academy recently migrated to **v2**, which features a decoupled architecture with a Vue 3 frontend and a FastAPI backend. The legacy Streamlit (v1) version is archived.

---

## ✨ Key Features

### 🎓 1. Student Learning Hub
* **📋 Daily Quests**: Interactive daily task manager with XP rewards (💎), Daily Boss Fights (👑), and screen-time balance indicators.
* **💬 Socratic AI Tutor ("Ask Floki")**: Gemini-powered AI tutor with interchangeable personas guiding students step-by-step.
* **🐾 Virtual Pets & Rewards**: Virtual pet companion mechanics and an XP Reward Store for real-world rewards.
* **🛠️ Creator Block**: Portfolio hub for hands-on engineering builds, coding projects, and video showcases.
* **📅 School Calendar**: Student view for live classes, kit delivery dates, field trips, and term milestones.

### 👨‍👧 2. Parent & Admin Dashboard
* **📝 Task Management & Lesson Scheduler**: Weekly grids and curriculum map scheduling.
* **📊 Analytics & Compliance**: Track subject mastery, weekly XP velocity, and generate proof-of-work academic portfolio reports.
* **💰 UFA & Scholarship Finances**: Expense tracking for state homeschooling scholarship funds (e.g., Arizona UFA/ESA).
* **🎁 XP Store Operations**: Manage reward inventories, costs, and redemption approvals.

---

## 🏗️ Architecture

Flokus Academy v2 uses a modern web stack:

* **Frontend (`/frontend`)**: Vue 3 + Vite + Pinia state management + Vue Router.
* **Backend (`/backend`)**: Python FastAPI + SQLAlchemy (asyncpg) + PostgreSQL.
* **AI Integration**: Google GenAI integration for the Socratic AI Tutor.

---

## 🚀 Quick Start & Installation

### Prerequisites
* Node.js 18+
* Python 3.10+
* PostgreSQL database

### 1. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup**: Create a `.env` file based on your environment needs (e.g., `DATABASE_URL`, `GEMINI_API_KEY`).
4. **Run the API**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend API will run on `http://localhost:8000`.

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```
2. **Install Dependencies**:
   ```bash
   npm install
   ```
3. **Run the Development Server**:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

---

## 🛡️ Privacy & Security
- Local database files, uploaded receipts, temporary scratch files, and `.env` secrets are strictly excluded via `.gitignore`.

## 📄 License
MIT License. Created for Flokus Academy.
