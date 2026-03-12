# 📃HabitFlow - Project Documentation

## 📋 Table of Contents
- [Project Overview & Problem Statement](#-project-overview--problem-statement)
- [Feature List & Scope Table](#feature-list--scope-table)
- [Architecture Diagram](#️-architecture-diagram)
- [Data Model (ERD / JSON Overview)](#data-model)
- [Emerging Tech Explanation (AI Categorization) ](#-emerging-tech-explanation-ai-categorization)
- [Setup & Run Instructions](#setup--run-instructions)
- [User Manual](#habitflow-user-manual)
- [Testing Summary](#testing-summary)
- [Team Roles & Contribution Matrix](#-team-roles--contribution-matrix)
- [Risk / Constraint Notes & Future Enhancements](#risk--constraint-notes--future-enhancements)
- [Individual Reflection ](#individual-reflection)

## Project Overview & Problem Statement

**HabitFlow** is an mobile habit tracker application that is safe and allows users to create regular routines and maintains their data confidential and easy to understand.A lot of available habit apps can be overly dependent on cloud storage, complex to use, or offer poor views of progress, which can discourage users to continue with their habits overtime.

The primary objectives of the project are to deliver easy habit creation and tracking, strong authentication using bcrypt, categorization of habits with AI help, and easy analytics that can be used by student, professionals and health conscious users.

## 🔗 Repository

**GitHub:** [https://github.com/lililhuan/Habit-Flow](https://github.com/lililhuan/Habit-Flow)

---
## 🔭 Feature List & Scope Table
| Area | Feature | In Scope | Notes |
|------|---------|----------|-------|
| Authentication | Registration, login, logout | Yes | Email/password with validation in the mobile app |
| Security | bcrypt password hashing, account lockout | Yes | 5 failed attempts, 15‑minute lockout, login logging. |
| Habit Managemnet | Create, edit, delete, activate/deactivate | Yes | 	Per‑user habit isolation and validation. | 
| Completion | Daily checklist and toggle completion | Yes | Tapping habit cards to mark completion on each day. |
| AI Categorization | Automatic category suggestion | Yes | On‑device rule‑based AI suggests categories as you type. |
| Analytics | Streaks, completion rates, category stats | Yes | Mobile stats view with streaks and category breakdowns.| 
| Theming | Light/dark themes and color options | Yes | Theme toggle inside Settings screen. | 
| Data Export | JSON export | Yes | Local backup from Settings to a JSON file. |
| Out of Scope | 	Cross‑device cloud sync, push notifications, web/desktop client. | No | Identified as future work for later versions.​ | 


## 🏗️ Architecture Diagram

![alt text](Architecture_Diagram.png)

## 📁 Folder Structure

```
Habit-Flow/
├── app/
│   ├── main.py                 # Entry point
│   ├── __init__.py
│   │
│   ├── components/             # Reusable UI components
│   │   ├── add_habit_dialog.py
│   │   ├── bottom_nav.py
│   │   └── habit_card.py
│   │
│   ├── config/                 # Configuration
│   │   └── theme.py            # Color themes
│   │
│   ├── models/                 # Data models
│   │   ├── habit.py
│   │   ├── completion.py
│   │   └── user.py
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── habit_service.py
│   │   ├── analytics_service.py
│   │   ├── export_service.py
│   │   ├── security_logger.py
│   │   └── ai_categorization_service.py  # Emerging Tech
│   │
│   ├── state/                  # State management
│   │   └── app_state.py
│   │
│   ├── storage/                # Data layer
│   │   └── database.py
│   │
│   ├── views/                  # UI screens
│   │   ├── welcome_view.py
│   │   ├── auth_view.py
│   │   ├── habits_view.py
│   │   ├── today_view.py
│   │   ├── stats_view.py
│   │   ├── settings_view.py
│   │   └── admin_view.py
│   │
│   └── tests/                  # Unit tests
│       ├── test_auth_service.py
│       ├── test_database.py
│       ├── test_habit_service.py
│       └── test_analytics_service.py
│
├── docs/                       # Documentation
├── storage/                    # Runtime data
├── requirements.txt
└── README.md
```

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Flet (Flutter for Python) | Cross-platform UI |
| **State** | Custom AppState | Singleton state management |
| **Backend** | Python 3.8+ | Business logic |
| **Database** | SQLite | Local data storage |
| **Security** | bcrypt | Password hashing |
| **AI** | Rule-based system | Habit categorization |
| **Testing** | pytest | Unit testing |
---


## Data Model

### 📊 Entity Relationship Diagram (ERD)

![alt text](ERD.png)

## 📋 Table Definitions

### 1. USERS Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user ID |
| email | TEXT | UNIQUE, NOT NULL | User email address |
| password_hash | TEXT | NOT NULL | bcrypt hashed password |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Registration date |

### 2. HABITS Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique habit ID |
| user_id | INTEGER | FOREIGN KEY → users(id) | Owner user |
| name | TEXT | NOT NULL | Habit name |
| frequency | TEXT | DEFAULT 'Daily' | 'Daily' or 'Weekly' |
| start_date | DATE | NOT NULL | Habit start date |
| color | TEXT | DEFAULT '#4A90E2' | Hex color code |
| icon | TEXT | DEFAULT '🎯' | Emoji icon |
| category | TEXT | DEFAULT 'Other' | AI-assigned category |
| is_archived | BOOLEAN | DEFAULT 0 | Archived flag |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation date |

### 3. COMPLETIONS Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique completion ID |
| habit_id | INTEGER | FOREIGN KEY → habits(id) | Parent habit |
| completion_date | DATE | NOT NULL | Date completed |
| notes | TEXT | NULL | Optional notes |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation |

**Unique Constraint:** (habit_id, completion_date) - One completion per habit per day

### 4. USER_SETTINGS Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique ID |
| user_id | INTEGER | UNIQUE, FOREIGN KEY → users(id) | Owner user |
| theme | TEXT | DEFAULT 'Default' | Theme name |
| dark_mode | BOOLEAN | DEFAULT 0 | Dark mode enabled |
| notifications_enabled | BOOLEAN | DEFAULT 1 | Notifications on/off |

### 5. SESSIONS Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique ID |
| user_id | INTEGER | UNIQUE, FOREIGN KEY → users(id) | User session |
| last_login | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last login time |

### 6. LOGIN_HISTORY Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique ID |
| user_id | INTEGER | FOREIGN KEY → users(id) | User who attempted |
| login_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | Attempt timestamp |
| success | BOOLEAN | NOT NULL | Login success/fail |
| ip_address | TEXT | NULL | IP address (if available) |

---

## 🔗 Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| Users → Habits | 1:N | One user can have many habits |
| Users → User_Settings | 1:1 | One user has one settings record |
| Users → Sessions | 1:1 | One user has one active session |
| Users → Login_History | 1:N | One user has many login attempts |
| Habits → Completions | 1:N | One habit has many completions |

---

## 📊 Sample Data

### Users
```json
{
  "id": 1,
  "email": "user@example.com",
  "password_hash": "$2b$12$...",
  "created_at": "2025-12-01T10:00:00"
}
```

### Habits
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Morning Exercise",
  "frequency": "Daily",
  "start_date": "2025-12-01",
  "color": "#10B981",
  "icon": "🏃",
  "category": "Health & Fitness",
  "is_archived": false
}
```

### Completions
```json
{
  "id": 1,
  "habit_id": 1,
  "completion_date": "2025-12-07",
  "completed": true,
  "notes": null
}
```
---
## 🤖 Emerging Tech Explanation (AI Categorization)

HabitFlow operates on a categorization engine that is AI-like and works on-device to propose a category as the user enters a name of a habit into the mobile app. This makes it easier to create habits since the user does not have to hand-think about categories, and it ensures that there are no conflicting categories since the analytics screen can calculate more accurate streaks and completion disaggregation. 

The engine is put as a rule based system that strategy is a mixture of dictionary of keywords, patterned regressions and fuzzy matching of the strings to rank each possible category and select the one that matches with the most confidence. All the operations occur locally on the Android/iOS device without any external API calls, which has the benefit of making the feature fast, private, and accessible offline, however at the cost of having the system not to automatically learn based on data and being most effective with English names of habits in its current state.

---
## 💻Setup & Run Instructions

HabitFlow is developed with Flet and SQLite and packaged as a mobile application for Android and iOS, while still supporting local development from source.

**For end users (Mobile build)**

- Install the Habitflow mobile application on an Mobile Devices using the provided build
- On first launch, create an account, then start adding and tracking habits directly from the mobile interface.

For Developers (run from source)
1. **Prerequisites**
 - Python 3.8 or Higher installed on your Pc/Laptop.
 - pip package manager and optionally Fit for cloning the repository
 2. Clone the repository

```bash
git clone https://github.com/lililhuan/Habit-Flow.git
cd Habit-Flow
```
3. Create virtual enviroment 

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```
**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
4. Install Dependencies 

```bash
pip install -r requirements.txt
```
this install Flet, bcrypt, pytest, and other requirements libraries

5. Configure environment 
- Copy .env.example to .env and adjust values such as database name and security setting if needed.
6.  Run the application
```bash
python app/main.py
```

Or using Flet CLI:
```bash
flet run app/main.py
```
this launches the app in a development enviroment so it can be tested or debug before mobile packaging.

7. Troubleshooting 
- If modules are missing, rerun pip install -r requirements.txt.

- If the database is locked or corrupted, delete the SQLite .db file so the app recreates it on next run.

- If Python is not recognized, ensure it is added to your system PATH.

---

# HabitFlow User Manual

## 1. Getting Started

### 1.1 Welcome Screen
![Welcome Screen](../docs/screenshots/01_welcome_view.png)

From the welcome screen you can:
- Read the key features: Daily Tracking, Streak Building, Progress Analytics.
- Tap **Create Account** to register, or **Sign In** if you already have an account.

### 1.2 Creating an Account
![Create Account](../docs/screenshots/02_create_account.png)

Steps:
- Enter a valid email address.
- Create and confirm your password.
- Make sure the password meets the requirements shown on screen (length and complexity).
- Tap **Create Account** to finish registration.

### 1.3 Signing In
![Sign In](../docs/screenshots/03_sign_in.png)

Steps:
- Enter the email and password you used at registration.
- Tap **Sign In** to open your HabitFlow dashboard.
- If you enter the wrong password too many times, your account may be temporarily locked as a security measure.

## 2. Main Navigation
![Main Navigation](../docs/screenshots/04_habits_view.png)

The bottom navigation bar contains:
- **Habits** – manage all your habits.
- **Today** – view and complete today’s habits.
- **Add (+)** – quickly add a new habit.
- **Stats** – see analytics and streaks.
- **Settings** – manage account, appearance, and data.

## 3. Core Features

### 3.1 Managing Habits
![Manage Habits](../docs/screenshots/04_habits_view.png)

- Tap **Add Habit** or **Add Your First Habit** to create a new habit.
- Use the list to review existing habits and open them for editing or deletion.

### 3.2 Adding a New Habit
![Add Habit](../docs/screenshots/06_add_habit.png)

Steps:
- Enter the Habit Name.
- Check the Category (AI) field; HabitFlow will suggest a category automatically based on the name, but you can change it manually.
- Choose a Frequency (Daily, Weekly, or Custom).
- Set the Start Date.
- Tap **Create Habit**.

### 3.3 Today View & Daily Tracking
![Today View](../docs/screenshots/05_today-view.png)

- The Today tab shows all habits scheduled for the selected date.
- Tap the checkbox on a habit card to mark it as complete.
- The progress bar and percentage at the top update automatically as you complete habits.

### 3.4 Analytics
![Analytics](../docs/screenshots/07_analytics_view.png)

The Stats tab shows:
- Total habits and total completions.
- Average completion rate and best streak.
- Weekly progress chart and habit performance summaries.

## 4. Settings & Personalization

### 4.1 Account Settings
![Account Settings](../docs/screenshots/08_settings_account.png)

From **Settings → Account** you can:
- View your email address.
- Sign out of your account.
- Change your password to keep your account secure.

### 4.2 Themes and Appearance
![Themes](../docs/screenshots/09_settings_theme.png)

From **Settings → Appearance** you can:
- Toggle Dark / Light Mode.
- Choose from multiple theme colors like Ocean Blue, Forest Green, Purple Dream, and more.
- See a live preview when a theme is applied successfully.

### 4.3 Data Management
![Data Management](../docs/screenshots/10_settings_data_management.png)

From **Settings → Data Management** you can:
- **Export Data** – download your habits and progress to a JSON file for backup.
- **Import Data** – restore from a previously exported backup.
- **Reset All Data** – remove all habits and completions but keep your account.
- **Delete Account** – permanently delete your account and all stored data.

### 4.4 About & Storage Information
![About](../docs/screenshots/11_settings_about.png)

The About section shows:
- App version.
- Short description of HabitFlow.
- Storage summary (total habits/completions, storage location = Local Device).

## 5. Admin Dashboard (for Admin Accounts)

### 5.1 User Management
![Admin Users](../docs/screenshots/12_admin_dashboard_users.png)

The Users tab in the Admin Dashboard lets administrators:
- View all registered users with their email and basic stats (for example, number of habits).
- See which accounts are marked as ADMIN.
- Perform actions such as view-only, disable, or delete a user account depending on what controls your build exposes.

### 5.2 Activity Monitoring
![Admin Activity](../docs/screenshots/13_admin_dashboard_activity.png)

The Activity tab shows recent login activity:
- A list of login events with email address and timestamp.
- A quick status label such as Success for successful logins.
- This view helps admins monitor whether accounts are being accessed as expected and supports manual security reviews.

### 5.3 Security Logs
![Admin Logs](../docs/screenshots/14_admin_dashboard_logs.png)

The Logs tab shows security-related events, such as:
- Successful logins, logouts, and sign‑ups.
- Failed login attempts that may indicate incorrect passwords or attempted brute‑force attacks.
- Each entry includes the event type, email, and timestamp, and can optionally be exported for auditing.

## 6. Security Features (User View)
Even though most security logic is behind the scenes, users should be aware of:
- **Password protection** – All passwords are stored as secure bcrypt hashes; plain text passwords are never saved.
- **Account lockout** – After several incorrect password attempts, the account may temporarily lock to protect against guessing attacks.
- **Local data storage** – All habits and progress are stored locally on the device; exporting and backing up data is under the user’s control.

Good practices:
- Use strong, unique passwords for HabitFlow.
- Regularly export your data if you plan to change or reset your device.

## 7. Tips for Effective Habit Tracking
- Start with a small number of habits (3–5) so you don’t feel overwhelmed.
- Set realistic frequencies (daily or a few times per week) instead of “perfect” schedules you can’t maintain.
- Check the Today view at a consistent time each day—morning or evening—to mark completions and review progress.
- Use the Stats tab weekly to see which areas you’re improving in and which ones need attention.

---

## 🧪Testing Summary
HabitFlow uses an automated test suite built with pytest and pytest-cov and manual testing of the mobile user interface. The automated tests are used to test the core business logic of authentication, database operations, habit management and analytics using an in-memory SQLite database in a manner that is isolated and repeatable.​

There are a total 62 automated tests in four major test files authentication, database, habit service and analytics service and they are all currently passing with an overall coverage of approximately 88 percent and each individual core modules coverage of 83-92 percent. To create an HTML coverage report, developers can run the suite at the project root with pytest -v to give detailed output or pytest --cov=app --cov-report=html to create an HTML coverage report and package new mobile builds.

---

## 👥 Team Roles & Contribution Matrix

HabitFlow was developed by three-member team, with one lead developer coordinating architeture and integration and two developers focusing on UI, database, security, and testing.

| Name | GitHub | Role | Main Focus Areas |
|------|--------|------|------------------|
| Roinel James Llesis | [@lililhuan](https://github.com/lililhuan) | Lead Developer | Project architecture, core habit and auth features, AI categorization, security controls, overall documentation. |
| Jeric Romace | [@titojek](https://github.com/titojek) | Developer | Mobile UI screens and components, navigation flow, testing and bug fixes, documentation support. | 
| Justine Aaron Sarcauga | [@JustineAaron](https://github.com/JustineAaron) | Developer | SQLite schema and queries, security logging, account management flows, testing and documentation support. |

## Contribution by Phase 

| Phase                    | Lead Contributors        | Notes                                                                           |
| ------------------------ | ------------------------ | ------------------------------------------------------------------------------- |
| Planning                 | All members      | Weekly meetings to refine scope and feature set. |
| Setup & Architecture     | Roinel James Llesis | Initial project structure and architectural decisions.​ |
| Core Feature Development | Roinel James Llesis | Habit CRUD, analytics, AI categorization, settings. |
| Security Implementation  | Jeric Romance          | bcrypt hashing, lockout logic, security logging.​ |
| UI/UX Development        | Justine Aaron Sarcauga          | Mobile layouts, navigation, theming |
| Testing                  | All members              | Unit tests, manual mobile testing, fixing defects.​|
| Documentation & Slides   | All members | Reports, docs folder, and final presentation. |

## ✅ Responsibilities Completed

### Roinel James LLesis (Lead Developer)
- [x] Set up project repository
- [x] Implement authentication system
- [x] Create habit management features
- [x] Build analytics dashboard
- [x] Develop AI categorization
- [x] Implement security features
- [x] Write unit tests
- [x] Create documentation

### Jeric Romance (Developer)
- [x] Database operations
- [x] Security logging
- [x] Account management
- [x] Test features
- [x] Bug fixes
- [x] Support documentation

### Justine Aaron Sarcauga (Developer)
- [x] Implement UI components
- [x] Create habit cards
- [x] Develop settings view
- [x] Test features
- [x] Fix UI bugs
- [x] Support documentation


## Risk / Constraint Notes & Future Enhancements

### ⚠️Risks and Mitigations of the project.

The primary technical and security risks of HabitFlow are the loss of data, compromised passwords, performance, and mobile device platform peculiarities. The risk of data loss is minimized with the help of SQLite and support of the JSON export backup, whereas the risk of the password breach is minimized with the help of the bcrypt hashing with the salt, strict password policies, and account lock-out option after several failures. Other security threats like brute-force attacks, SQL injections and session grabbing are addressed using lockout settings, query parameters and sensitively handling sensitive information in memory. 

### 🚧Constraints

The project is limited to a local-only SQLite storage, i.e. data is stored on one mobile device with no inbuilt cloud sync. The other limitations are the limited amount of time to develop in a semester, the team size of three people, Material Design 3 UI choice, only English-only interface, and test on devices and emulators that the group had. 

### 🔮Future Enhancements

The intended improvements aim at enhancing the current mobile version with future expansion in terms of features and scalability. Short-term focus will be added cloud backup and sync, push notifications or reminders, and more refined mobile builds and widgets, and medium-term will be social features, gamification, calendar integration, and ML-based predictions of habit success. In the long term, the ideas include an AI-based coach, integration with wearables, enterprise/team-level, even better security with 2-factor or bio-metric authentication, and optional migration to cloud databases and CI/CD pipelines as the application grows.

## Individual Reflection

### 👨‍💻Roinel James Llesis 

**Learning Reflection**

This project altered my perception of application development, as well as my learning process. Until HabitFlow, I largely considered an app to be a set of features, here I saw the extent to which there are numerous layers, design, security, testing, documentation, and teamwork are all occurring simultaneously. I experienced the contrast between merely going through a tutorial and making decisions, troubleshooting problems that were not that self-evident, and having to live with those choices throughout the project. Mentally it was at times exhausting, yet it taught me to be less impatient and more interested in finding out how things actually work behind the scenes.

Among the largest lessons that I got was the value of iteration. The concepts which seemed perfect in my headhead had to be simplified or redone after we had tried them in the application. I came to value feedback and view bugs as opportunities to learn rather than to fail and apply tests and documentation as an opportunity to learn more about the system. Collaborating with colleagues also allowed me to learn more about the importance of communicating more effectively, seeking assistance sooner, and relying on the strengths of other employees. In general, this project has allowed me to feel more comfortable in complex and uncertain situations and enhance my drive to continue learning how to develop better and more secure applications.

---

### 👨‍💻Jeric Romance 

**Learning Reflecetion**

For me, The project was mainly about learning how to think of data and reliability. I was more enlightened that any design choice comes with effects of determining its ease of storage, recall and reliability with time. Using a real database helped me observe structure such as relationships, constraints and edge cases when working in small tasks that we do not always see. It made me go ahead and ask questions like what would happen when the user erases this? or "How can we ensure records remain consistent that transformed my approach to problems overall.

I also was taught much about my learning style. I observed that I got more mistakes whenever I attempted to hurry and anything that concerned data. The need to slow down and read errors carefully, sketch schemes, and ask the team to talk over ideas actually helped to save time in the long run. The project demonstrated to me that it is not bad to be ignorant of something initially, provided that I am ready to research, test and revise my knowledge. It also helped me to value teamwork, as most of the solutions that were good were achieved through discussions and not by an individual. This experience made me continue developing my knowledge in the direction of backend and data-related subjects and remain receptive to feedback and new ideas.

---
### 👨‍💻Justine Aaron Sarcauga

**Learning Reflection**

HabitFlow turned out to be an educational process of how users experience software in their real life. I began to notice things that I previously ignored, like the number of steps required to accomplish something, whether the labels are easy to understand, and the layouts on a small screen. I noticed that the slightest modification of the wording or the position could make or break the app; it would be either more comfortable or more difficult. This got me paying closer attention not just to our project, but also to the apps that I use on a daily basis and I started to give myself a reverse-engineering of why some designs feel more comfortable than others.

The other significant aspect of my learning was the way to work out frustration constructively. Sometimes the designs failed to do the required job or some alterations caused frustration on another design and the initial thought that came to my mind was that I was caught in between. Gradually I came to know that it is better to divide any problem into small parts, experiment with ideas, discuss others with me and not attempt to solve everything myself. I also began to value testing and documentation as a means to aid in learning since they compel you to have a clear understanding of what the software is supposed to accomplish. The project made me feel even more confident that I will continue to become a better developer, particularly in the area of developing user-friendly applications.

---
