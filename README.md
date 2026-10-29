# Iskolar ng Bayan

**AI-Assisted Scholarship Applicant Screening and Management System**, designed for the Local Youth Development Office (LYDO) of Santa Cruz, Laguna.

This is the desktop edition (Python + PyQt6). The web edition, a FastAPI backend and React interface built on this same code, lives in [IskoMatic](https://github.com/choivxcz/IskoMatic).

## What it does

- **Registration**: an applicant and their application are entered in one guided, validated flow, including exam scores and household details.
- **AI screening**: a Random Forest model scores each pending application from 13 academic and household factors and returns a probability and a recommendation. The recommendation is **advisory only**: the system never awards or rejects a scholarship by itself.
- **Re-screening only when needed**: each result stores a fingerprint of its inputs and the model version, so unchanged applications aren't re-scored.
- **Review workflow**: reviewer decisions (endorse, waitlist, or reject), then interviews and official decisions.
- **Archive**: records are archived instead of deleted, so past applicants and outcomes stay searchable.

## Tech

Python · PyQt6 · MySQL · scikit-learn · pandas · joblib

## Getting started

Requires Python 3.12+ and a MySQL server.

```bash
pip install -r requirements.txt

# 1. Create the database and tables
mysql -u root -p < schema.sql

# 2. Add your database credentials
cp .env.example .env          # then set DB_USER and DB_PASSWORD

# 3. Run the app
python main.py
```

The trained model is included in `models/`. To retrain it from `isko.csv`:

```bash
python train_ml_model.py
```

### Tests

The tests use a real MySQL connection configured through `.env`.

```bash
pip install pytest
python -m pytest
```

## Project structure

```
app/
  repositories/   MySQL data access (applicants, applications, interviews, decisions, results)
  services/       Application rules, ML screening, and result persistence
  ui/             PyQt6 main window, pages, and forms
database/         Connection settings (read from .env)
models/           Saved Random Forest model (versioned)
tests/            Repository, service, and screening tests
schema.sql        Database schema
isko.csv          Synthetic training data (no real applicants)
train_ml_model.py Trains and saves the model with its evaluation metrics
```

## Data and privacy

The repository contains no real applicant data. `isko.csv` is a synthetic dataset, and local database backups (`backups/`) and `.env` files are git-ignored so personal information and credentials never get committed.

---

Built by [Karl Cuerdo](https://github.com/choivxcz).
