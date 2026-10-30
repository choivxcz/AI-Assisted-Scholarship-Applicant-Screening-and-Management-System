# Iskolar ng Bayan: AI-Assisted Scholarship Applicant Screening and Management System

## Overview

Iskolar ng Bayan is a desktop information system designed for the Local Youth Development Office (LYDO) of Santa Cruz, Laguna. It supports the office in registering scholarship applicants, screening their applications, and recording interviews and final decisions. A machine learning model assists the screening process by estimating the likelihood that an application meets the program's criteria.

This repository contains the desktop edition, developed in Python with PyQt6. A web edition built on the same code base, with a FastAPI back end and a React interface, is maintained in [IskoMatic](https://github.com/choivxcz/IskoMatic).

## Objectives

1. To provide a single, validated process for registering applicants and their applications.
2. To assist reviewers with a consistent, data-driven screening recommendation.
3. To keep a complete record of reviews, interviews, and decisions, including those of past applicants.

## Features

1. Registration. Each applicant and application, including examination scores and household information, is entered through a single guided form with input validation.
2. AI-assisted screening. A Random Forest classifier evaluates each pending application on 13 academic and household factors and returns a probability and a recommendation. The recommendation is advisory: the system does not award or reject a scholarship on its own, and final decisions remain with the office.
3. Selective re-screening. Each screening result stores a fingerprint of its inputs and the model version, so applications that have not changed are not evaluated again.
4. Review workflow. Reviewers may endorse, waitlist, or reject an application, after which interviews and official decisions are recorded.
5. Archiving. Records are archived rather than deleted, so past applicants and their outcomes remain searchable.

## Technologies Used

- Python 3.12
- PyQt6 (graphical user interface)
- MySQL (database)
- scikit-learn, pandas, and joblib (machine learning)

## Installation and Usage

Python 3.12 or later and a MySQL server are required.

```bash
pip install -r requirements.txt
```

1. Create the database and its tables.

   ```bash
   mysql -u root -p < schema.sql
   ```

2. Copy `.env.example` to `.env` and set `DB_USER` and `DB_PASSWORD`.

3. Start the application.

   ```bash
   python main.py
   ```

A trained model is included in `models/`. To retrain it from `isko.csv`:

```bash
python train_ml_model.py
```

## Testing

The tests connect to a MySQL database configured through `.env`.

```bash
pip install pytest
python -m pytest
```

## Repository Structure

```
app/
  repositories/      MySQL data access (applicants, applications, interviews, decisions, results)
  services/          Application rules, machine learning screening, and result storage
  ui/                PyQt6 main window, pages, and forms
database/            Connection settings (read from .env)
models/              Saved Random Forest model (versioned)
tests/               Repository, service, and screening tests
schema.sql           Database schema
isko.csv             Synthetic training data
train_ml_model.py    Trains the model and saves it with its evaluation metrics
```

## Data Privacy

This repository contains no real applicant data. The training set `isko.csv` is synthetic. Local database backups (`backups/`) and `.env` files are excluded from version control so that personal information and credentials are not committed.

## Author

Karl Sebastian V. Cuerdo
