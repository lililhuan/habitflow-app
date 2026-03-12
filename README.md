# 🎯 HabitFlow - Habit Tracking Application

**Track your habits. Stay consistent. Build a better you.**

HabitFlow is a mobile habit tracking application built with Flet (Python) to help users build  their consistent habits and track their progress

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-0.23+-green.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Security Features](#-security-features)
- [AI Categorization](#-ai-categorization-emerging-tech)
- [Installation](#-installation)
- [Usage](#-usage)
- [Running Tests](#-running-tests)
- [Project Structure](#-project-structure)
- [Technology Stack](#-technology-stack)
- [Documentation](#-documentation)
- [Team Members](#-team-members)

---

## 🌟 Features

### Core Features
| Feature | Description |
|---------|-------------|
| 👤 **User Authentication** | Secure sign-up/sign-in with password validation |
| 📝 **Habit Management** | Create, edit, delete, and track daily/weekly habits |
| ✅ **Daily Tracking** | Mark habits complete with date navigation |
| 🔥 **Streak Building** | Track current and longest streaks |
| 📊 **Progress Analytics** | Visualize progress with charts and statistics |
| 💾 **Data Export/Import** | Backup and restore your data (JSON format) |
| 🎨 **Theme Support** | 8 color themes + dark/light mode |
| 🤖 **AI Categorization** | Automatic habit categorization using AI |
| 👨‍💼 **Admin Dashboard** | User management for administrators |

### Analytics & Visualization
- 📊 Completion rate tracking
- 🔥 Streak calculations (current & longest)
- 📈 Weekly pattern analysis
- 🏆 Habit performance ranking
- 📅 Monthly/yearly statistics
- 📊 Category distribution charts

---

## 🔐 Security Features

### Authentication & Authorization
- ✅ **Password Hashing** - bcrypt encryption for all passwords
- ✅ **Password Requirements** - Minimum 8 chars, uppercase, number
- ✅ **Account Lockout** - 5 failed attempts = 15 min lockout
- ✅ **Session Management** - Auto-logout after inactivity
- ✅ **Admin Access Control** - Role-based admin privileges

### Logging & Monitoring
- 📝 **Security Logs** - Track login attempts, password changes
- 📝 **Activity Logs** - Monitor user activity
- 📝 **Failed Login Tracking** - Detect brute force attempts

### Data Protection
- 🔒 Local SQLite database (no cloud transmission)
- 🔒 Thread-safe database connections
- 🔒 Input validation and sanitization

---

## 🤖 AI Categorization (Emerging Tech)

HabitFlow uses **AI-powered automatic categorization** to organize your habits intelligently.

### How It Works
1. User types habit name (e.g., "Go to gym")
2. AI analyzes keywords and patterns
3. Category is auto-suggested (e.g., "🏃 Fitness")
4. User can accept or change the suggestion

### Supported Categories
| Category | Example Habits |
|----------|----------------|
| 🏃 **Fitness** | Go to gym, Run 5km, Workout |
| 📚 **Education** | Read a book, Study Python, Learn Spanish |
| 🧘 **Mindfulness** | Meditate, Practice gratitude, Deep breathing |
| 💼 **Work** | Finish report, Email clients, Update resume |
| 🥗 **Health** | Drink water, Take vitamins, Sleep 8 hours |
| 👥 **Social** | Call mom, Meet friends, Text family |
| 💰 **Finance** | Save money, Track expenses, Review budget |
| 🎨 **Other** | Default for unrecognized habits |

### Implementation
- **Rule-based pattern matching** with keyword dictionaries
- **Regex patterns** for flexible matching
- **Confidence scoring** for accuracy
- **Fallback category** for unrecognized habits

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/lililhuan/Habit-Flow.git
   cd Habit-Flow/app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   flet run
   ```
   
   Or using Flet CLI:
   ```bash
   flet run app/main.py
   ```

---

## 📱 Usage

### First Time Setup
1. Launch the app
2. Click "Create Account"
3. Enter email and password (must meet requirements)
4. Add your first habit with the + button
5. Start tracking daily!

### Navigation
| Icon | Tab | Description |
|------|-----|-------------|
| 🏠 | **Habits** | View and manage all habits |
| ✓ | **Today** | Track today's habits |
| ➕ | **Add** | Create a new habit |
| 📊 | **Stats** | View analytics and charts |
| ⚙️ | **Settings** | Account, themes, data management |

### Admin Access
- Admin emails are configured in the app
- Admins can: view all users, disable accounts, view security logs

---

## 🧪 Running Tests

HabitFlow includes **62 unit tests** with ~88% code coverage.

### Run All Tests
```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing
```

### Test Files
| File | Tests | Coverage |
|------|-------|----------|
| `test_auth_service.py` | 15 | Authentication, password hashing |
| `test_database.py` | 12 | CRUD operations, constraints |
| `test_habit_service.py` | 20 | Habit management, AI categorization |
| `test_analytics_service.py` | 15 | Statistics, streaks |

---

## 📁 Project Structure

```
Habit-Flow/
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── pytest.ini             # Test configuration
│
├── app/
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   │
│   ├── components/        # Reusable UI components
│   │   ├── add_habit_dialog.py
│   │   ├── bottom_nav.py
│   │   └── habit_card.py
│   │
│   ├── config/            # Configuration files
│   │   └── theme.py       # Color themes
│   │
│   ├── models/            # Data models
│   │   ├── habit.py
│   │   ├── completion.py
│   │   └── user.py
│   │
│   ├── services/          # Business logic
│   │   ├── auth_service.py
│   │   ├── habit_service.py
│   │   ├── analytics_service.py
│   │   ├── export_service.py
│   │   └── security_logger.py
│   │
│   ├── state/             # Application state
│   │   └── app_state.py
│   │
│   ├── storage/           # Database layer
│   │   └── database.py
│   │
│   ├── views/             # UI screens
│   │   ├── welcome_view.py
│   │   ├── auth_view.py
│   │   ├── habits_view.py
│   │   ├── today_view.py
│   │   ├── stats_view.py
│   │   ├── settings_view.py
│   │   └── admin_view.py
│   │
│   └── tests/             # Unit tests
│       ├── __init__.py
│       ├── test_auth_service.py
│       ├── test_database.py
│       ├── test_habit_service.py
│       └── test_analytics_service.py
│
├── storage/               # Runtime data
│   └── data/
│
└── assets/                # Static assets
```

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| **Framework** | Flet (Flutter for Python) |
| **Language** | Python 3.8+ |
| **Database** | SQLite |
| **Authentication** | bcrypt |
| **UI/UX** | Material Design 3 |
| **State Management** | Custom AppState |

---

## 📚 Documentation


Full documentation and Info Assurance report are available in:
- [`docs/PDF/`](docs/PDF/) — Project report, Info Assurance documentation, and PDF deliverables
- [`docs/README.md`](docs/README.md) — Markdown documentation, architecture, features, data model, team, reflections, etc.
- [`docs/screenshots`](docs/screenshots) — screenshot of UI

### Key Documentation Files
| Document | Description |
|----------|-------------|
| [Project Overview & Problem Statement](docs/README.md#project-overview--problem-statement) | Problem, objectives |
| [Feature List & Scope Table](docs/README.md#feature-list--scope-table) | Features in/out of scope |
| [Architecture Diagram](docs/Architecture_Diagram.png) | System architecture (PNG) |
| [Database ERD](docs/ERD.png) | Database schema (PNG) |
| [User Manual](docs/README.md#habitflow-user-manual) | Feauture guides for regular user and admin user |
| [Testing Summary](docs/README.md#testing-summary) | Test plan, coverage |
| [Team Contributions](docs/README.md#team-roles--contribution-matrix) | Roles, matrix |
| [Future Enhancements](docs/README.md#risk--constraint-notes--future-enhancements) | Risks, future work |
| [Individual Reflection](docs/README.md#individual-reflection) | Team reflections |

---



## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/lililhuan/Habit-Flow.git
cd Habit-Flow

# 2. Install
pip install -r requirements.txt

# 3. Run
flet run main.py

# 4. Test
pytest -v
```

---

## 👥 Team Members

| Name | Role | GitHub |
|------|------|--------|
| **Roinel James LLesis** | Lead Developer | [@lililhuan](https://github.com/lililhuan) |
| **Jeric Romance** | Developer | [@titojek](https://github.com/titojek) |
| **Justine Aaron Sarcauga** | Developer | [@JustineAaron](https://github.com/JustineAaron) |

---

## 📄 License

This project is developed as an academic project for **Application Development**, **Information Assurance**, and **Software Engineering courses** at **Camarines Sur Polytechnic Colleges**.

---

## 🙏 Acknowledgments

- [Flet](https://flet.dev/) - Cross-platform UI framework
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing library
- [pytest](https://pytest.org/) - Testing framework

---

**Made with ❤️ for building better habits**
