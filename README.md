# Job Hunt Dashboard

An automated, AI-powered workspace to discover, score, and track remote job opportunities. This repository contains the backend scrapers, AI scoring pipelines, and a React-like visual Kanban dashboard to manage your job applications. 

## 🚀 Features

- **Automated Discovery**: Scrape remote jobs from sources like Remotive, WeWorkRemotely, LinkedIn, Wellfound, and more.
- **AI Scoring Pipeline**: Uses Google's Gemini to assess job descriptions against your personal profile and skills log. It returns a score (0-100) and a breakdown of matches/mismatches.
- **Kanban Dashboard**: A local web interface to visualize jobs as they flow from "New" to "Shortlisted", "Applied", "Closed", or "Graveyard".
- **AI Tailoring**: Automatically generate tailored Resumes and Cover Letters for highly-scored jobs using Gemini.
- **Exporting**: Save tailored documents directly to PDF.
- **Skills Intelligence**: Generates a heatmap of demanded skills/tools across your discovered jobs.

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, SQLite
- **AI Integration**: Google GenAI SDK (Gemini-3-flash / flash-lite)
- **Scraping**: `jobspy`, `requests`, `urllib`
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (No build step required)

## 📦 Setup & Installation

### ⚡ Quick Start (Recommended)

The easiest way to set up the project is using the interactive Setup Wizard:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/job-hunt.git
   cd job-hunt
   ```
2. **Open the project in VS Code:**
   ```bash
   code .
   ```
3. **Run the Wizard:**
   - Go to the top menu: **Terminal** → **Run Task...**
   - Select **`⚙️ Run Setup Wizard`**
   - Follow the interactive prompts to build your profile and search queries!

---

### 🛠️ Manual Setup (For Advanced Users)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/job-hunt.git
   cd job-hunt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Environment:**
   - Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.
   - Copy `data/user_profile.example.md` to `data/user_profile.md` and fill in your identity, background, and career goals.
   - Drop your base markdown resume into `data/base_resume.md`.

## ⚙️ Usage

The system is controlled via the `run.py` Command Line Interface (CLI).

### 1. Discover & Score New Jobs
Scrape enabled job boards. The script will automatically score any unscored jobs in the database against your `user_profile.md`.

```bash
python run.py discover --deep
```

### 2. Launch the Dashboard
Start the local Flask server and open the Kanban board in your web browser.

```bash
python run.py dashboard --port 8080
```

### 3. Generate a Skill Report
Run the global intelligence script to see which keywords are trending in your scraped jobs.

```bash
python run.py report
```

## 🔒 Privacy

This repository is designed as a template. Your personal config files (`.env`, `data/user_profile.md`, `data/base_resume.md`, `data/jobs.db`, `data/skills_log.json`, `data/.personal_info`) are excluded via `.gitignore` and remain strictly on your local machine.

## 📄 License

MIT License. See `LICENSE` for more information.
