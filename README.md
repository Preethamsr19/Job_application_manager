# CareerTrack — Job Application Management System

CareerTrack is a web-based application designed to help job seekers organize and track their job search in one place. Built using Python, Flask, MySQL, HTML, and CSS, it provides a centralized dashboard to manage job applications, assessments, interviews, preparation tasks, and notes.

## Features

- **User Authentication:** Register, log in, and manage authenticated sessions.
- **Dashboard:** View application statistics, upcoming assessments, interviews, and pending preparation tasks.
- **Company Management:** Manage company records associated with job applications.
- **Application Tracking:** Track job roles, application dates, status, salary, location, and job links.
- **Assessment Tracking:** Record assessment details, dates, platforms, and completion status.
- **Interview Management:** Organize interview schedules, types, modes, meeting links, and feedback.
- **Preparation Tasks:** Create and manage tasks with due dates, priorities, and completion statuses.
- **Application Notes:** Create, edit, and delete notes to keep important job-search information organized.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Database Connectivity:** MySQL Connector
- **Tools:** Visual Studio Code, Git, GitHub

## Project Structure

```text
job_application_manager/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── routes.py
│   └── extra_routes.py
├── database/
│   └── schema.sql
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── applications.html
│   ├── assessments.html
│   ├── dashboard.html
│   ├── interviews.html
│   ├── login.html
│   ├── notes.html
│   ├── register.html
│   └── tasks.html
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

## Database Design

The application uses MySQL with the following tables:

| Table | Purpose |
|---|---|
| `users` | Stores user account information |
| `companies` | Stores company records |
| `applications` | Tracks job applications |
| `assessments` | Stores assessment details |
| `interviews` | Stores interview information |
| `tasks` | Manages preparation tasks |
| `notes` | Stores application-related notes |

## Getting Started

### Prerequisites

Install the following before running the project:

- Python 3
- MySQL Server
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Preethamsr19/Job_application_manager.git
cd Job_application_manager
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Create the database named `job_application_manager` in MySQL and execute the SQL statements in `database/schema.sql`.

Configure the following environment variables in PowerShell, replacing the example password with your own MySQL password:

```powershell
$env:MYSQL_HOST = "localhost"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "your_actual_mysql_password"
$env:MYSQL_DATABASE = "job_application_manager"
$env:SECRET_KEY = "replace-with-a-random-secret"
```

Use the MySQL username and database settings configured on your system if they differ from these examples.

### 5. Run the application

```powershell
python run.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

## Learning Outcomes

This project demonstrates practical implementation of:

- Flask application structure and routing
- REST API development
- MySQL database design and integration
- CRUD operations
- User authentication and session management
- Frontend and backend integration
- Organizing a multi-feature web application

## Future Improvements

- Add application search and advanced filtering.
- Introduce reminders for upcoming assessments and interviews.
- Add data export and application analytics.
- Improve dashboard visualizations and user experience.

## Author

**Preetham S R**

GitHub: [Preethamsr19](https://github.com/Preethamsr19)