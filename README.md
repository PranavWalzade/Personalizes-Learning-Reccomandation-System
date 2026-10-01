# LearnAI: Personalized Learning Recommendation System

LearnAI is a personalized learning platform designed to help students discover relevant courses, understand their skill gaps, and follow a guided learning path based on their academic profile and interests.

The system combines a Flask backend, a MySQL-backed data layer, and a browser-based frontend to provide a complete student learning experience.

## Features

- Student registration and login
- Personalized course recommendations
- Skill gap analysis
- Learning path planning
- Academic dashboard and progress tracking
- Course enrollment, status updates, and removal from My Courses
- Course and profile management APIs
- AI/ML-informed recommendation support using dataset-driven analysis

## Tech Stack

- Python
- Flask
- MySQL
- scikit-learn, pandas, NumPy, SciPy
- Matplotlib / Seaborn for analysis and reporting
- HTML, CSS, and JavaScript for the frontend

## Project Structure

```text
Personalized_Learning/
├── .env                          # Local database configuration
├── requirements.txt             # Python dependencies
├── start_learnai.bat            # Windows launcher for backend + browser
├── app/
│   ├── backend/
│   │   ├── app.py               # Flask application entry point
│   │   ├── config.py            # Backend configuration
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic/helpers
│   │   ├── utils/               # Database helper and utilities
│   │   └── ...
│   └── frontend/
│       ├── index.html           # Landing page
│       ├── css/                 # Styling
│       ├── js/                  # Frontend logic
│       └── pages/               # App pages
├── src/
│   ├── config.py                # ML/data setup configuration
│   ├── check_setup.py           # Setup validation script
│   ├── preprocessing/           # Data cleaning/transformation
│   ├── recommendation/          # Recommendation logic
│   ├── validation/              # Validation scripts
│   └── ...
├── data/                        # Project datasets
├── models/                      # Saved ML models
├── reports/                     # Generated reports
├── plots/                       # Chart outputs
├── exports/                     # Exported data/files
├── logs/                        # Logs
├── results/                     # Recommendation outputs
└── README.md
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.10 or newer
- MySQL Server installed and running
- A MySQL database named `personalized_learning`
- Access to the project virtual environment or a local Python environment

## Setup

1. Open a terminal in the project root.
2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment:

- Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

- Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Configure the database in `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=personalized_learning
```

6. Make sure the MySQL database exists and has the required tables for the app.

## Running the application

### Option 1: Use the provided Windows launcher

```cmd
start_learnai.bat
```

This script starts the backend and opens the app in the browser.

### Option 2: Run manually

From the project root:

```bash
python app/backend/app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## Main API Endpoints

The application exposes a set of routes under `/api`, including:

- `POST /api/register`
- `POST /api/login`
- `GET /api/health`
- `DELETE /api/student/<student_id>/courses/<course_code>` to remove an enrollment and its saved progress
- course-related endpoints
- profile and dashboard routes
- recommendations and skill-gap routes
- learning path endpoints

## Notes

- The app uses a MySQL connection via `mysql-connector-python`.
- The backend serves the static frontend files from `app/frontend`.
- The ML and analytics pipeline lives under `src/` and is used to support the recommendation system.

## Website recommendation model

The website loads the fitted `TfidfVectorizer` from
`models/content_based_tfidf.joblib`. The vectorizer was trained on the engineering
course catalog's names, branches, categories, skills, prerequisites, and course
levels. At recommendation time, the backend compares that course content with
the signed-in student's interests, branch, learning level, and saved skills,
then combines the content similarity with profile compatibility, semester fit,
and difficulty fit to rank courses.

The model is used directly by `GET /api/student/<student_id>/recommendations`.
If the trained artifact is missing or unreadable, the endpoint returns an error
instead of silently substituting a different model. The TF-IDF similarity is a
content relevance score, not a prediction of grades, course completion, or
learning outcomes. The OULAD collaborative-filtering benchmark in
`models/model_manifest.json` is an offline evaluation and is not mapped directly
to the engineering course IDs shown in the website.

If the course catalog is empty after database setup, load the included catalog:

```powershell
.\.venv\Scripts\python.exe app\backend\load_courses.py
```

## Development Notes

This project is structured as a learning/research application. It is useful for:

- experimenting with student personalization logic
- analyzing learning behaviors and skills
- building recommendation flows for course selection
- prototyping an educational dashboard and planner

## License

This project is intended for educational and academic use. Please verify license requirements for any datasets or third-party assets included in the repository before redistribution or commercial use.
