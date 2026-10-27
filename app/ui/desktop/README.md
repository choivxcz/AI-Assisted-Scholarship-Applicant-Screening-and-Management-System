# Iskolar ng Bayan — React + TypeScript + Tauri desktop UI

This desktop UI lives under `app/ui/desktop/`. It reuses the project's existing Python repositories and services and does not create or migrate database tables. It replaces the former PyQt6 frontend; the Python backend and database scripts are preserved.

## Windows prerequisites

1. Node.js LTS: https://nodejs.org/
2. Rust stable via rustup: https://www.rust-lang.org/tools/install
3. Visual Studio Build Tools with **Desktop development with C++**: https://visualstudio.microsoft.com/visual-cpp-build-tools/
4. WebView2 Runtime (normally already installed on Windows 10/11): https://developer.microsoft.com/microsoft-edge/webview2/
5. The project's existing Python environment and dependencies. Keep the project-root `.env` configured with `DB_USER` and `DB_PASSWORD`.

Restart VS Code after installing the tools. Verify with `node -v`, `npm -v`, `rustc --version`, `cargo --version`, and `python --version`.

## Start development app

Open the project root (the folder containing `main.py`, `app/`, and `database/`) in VS Code. Activate the same Python virtual environment used by the current PyQt6 app, then run:

```powershell
cd app/ui/desktop
npm install
npm run tauri dev
```

Tauri launches a native Windows window and starts `bridge_server.py`, which binds only to `127.0.0.1:8765`. If you need to start the bridge manually for debugging, run `python app/ui/desktop/bridge_server.py` from the project root in a separate terminal, then run `npm run tauri dev` in the desktop folder. Do not start two bridge instances on the same port.

## Connected workflows

- Live dashboard and active applicant/application/interview/decision records from MySQL.
- Register an applicant and scholarship application together using `ApplicationService.register_applicant_with_application`.
- Edit applicant details and archive an applicant using the existing repository methods.
- Edit application eligibility data and change status using the existing repository/service validation.
- Run and persist AI screening through `ScreeningPersistenceService` and the saved model.
- Schedule interviews for `FOR_INTERVIEW` applications and save interview outcomes.
- Record scholarship decisions using `ScholarshipDecisionRepository.save`.

AI screening output is advisory only. The interface does not automatically award or reject scholarships.

## Build installer

```powershell
npm run tauri build
```

The Windows installer is generated under `src-tauri/target/release/bundle/`. Packaging Python, its dependencies, the model file, and local MySQL configuration for another computer is a separate deployment step. Never ship a real `.env` password inside a distributable installer.

Keep the project-root `.env` local. No database migrations or schema changes are required by this frontend replacement.
