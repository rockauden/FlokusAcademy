# 🎓 Flokus Academy — Master Homeschooling LMS & Operating System

**Flokus Academy** is a comprehensive, gamified Learning Management System (LMS) and homeschooling dashboard built for 5th-grade instruction. It synchronizes a 9-program curriculum suite into a single interface, balancing core academic hubs, applied STEM spokes, XP gamification, AI Socratic tutoring, and parental compliance tracking.

---

## ✨ Key Features

### 🎓 1. Student Learning Hub
* **📋 Daily Quests**: Interactive daily task manager with XP rewards (💎), Daily Boss Fights (👑), and screen-time balance indicators.
* **💬 Socratic AI Tutor ("Ask Floki")**: Gemini-powered AI tutor with interchangeable personas (**Norse Boatbuilder**, **Space Robot**, **Socratic Tutor**) guiding students step-by-step.
* **🐾 Pet Arena ("Sparky")**: Virtual pet companion mechanics—feed, train, participate in trivia battles, and explore dungeon zones as reward incentives.
* **🛠️ Creator Block**: Portfolio hub for hands-on engineering builds, coding projects, and video showcases.
* **🛍️ XP Reward Store**: Redeem earned XP for real-world rewards, screen-time passes, or custom family incentives.
* **📅 School Calendar**: Student view for live classes, kit delivery dates, field trips, and term milestones.

### 👨‍👧 2. Parent & Admin Dashboard
* **📝 Task Management & Lesson Scheduler**:
  * **⚡ Quick Add**: Instant single-lesson scheduler.
  * **📅 Weekly Grid & Screen-Time Audit**: Visual 5-day workload grid with real-time **Offline 📖 vs. Online 💻 screen-time balance auditing**.
  * **⚙️ Master Curriculum Scheduler (Tier 1 & Tier 2)**: 1-click batch scheduler driven by the 36-week / 9-unit master curriculum map.
* **📊 Analytics & Compliance**: Track subject mastery, weekly XP velocity, and generate proof-of-work academic portfolio reports.
* **💰 UFA & Scholarship Finances**: Expense tracking for state homeschooling scholarship funds (e.g., Arizona UFA/ESA), category caps, and receipt management.
* **🎁 XP Store Operations**: Manage reward inventories, costs, and redemption approvals.

---

## 🧩 9-Program Master Curriculum Integration

Flokus Academy synchronizes 9 core academic programs across 4 quarters and 9 unit blocks:

```
Core Foundational Hubs                   Applied Project Spokes
----------------------                   ----------------------
🧮 Math: Beast Academy                   🧪 STEM: CrunchLabs Build Boxes
✍️ Language Arts: Brave Writer Dart       🏫 Electives: Outschool Live Classes
🗺️ History: Tuttle Twins America          ⚔️ Interactive STEM: Brilliant.org
🧠 Critical Thinking Co.                 🤖 Strategy & AI: Synthesis
                                         ♟️ Strategy & Tactics: Chess.com
```

---

## 🚀 Quick Start & Installation

### Prerequisites
* Python 3.10+
* Streamlit

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rockauden/FlokusAcademy.git
   cd FlokusAcademy
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Secrets (Optional for AI Tutor)**:
   Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your_google_gemini_api_key"
   admin_pin = "1234"
   ```

4. **Launch the Application**:
   ```bash
   streamlit run app.py
   ```
   Or run using the provided Windows batch script:
   ```cmd
   run_flokus.bat
   ```

---

## 🛡️ Privacy & Security
- Local database files (`*.db`), uploaded receipts, temporary scratch files, and API keys (`.streamlit/secrets.toml`) are strictly excluded via `.gitignore`.

---

## 📄 License
MIT License. Created for Flokus Academy.
