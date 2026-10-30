#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{fs::OpenOptions, path::{Path, PathBuf}, process::{Child, Command, Stdio}, sync::Mutex};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use tauri::Manager;

struct BridgeProcess(Mutex<Option<Child>>);

fn project_root() -> PathBuf {
    // src-tauri -> desktop -> ui -> app -> project root
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../").canonicalize().unwrap_or_else(|_| PathBuf::from("."))
}

fn python_executable(root: &Path) -> PathBuf {
    let local = if cfg!(windows) {
        root.join(".venv").join("Scripts").join("python.exe")
    } else {
        root.join(".venv").join("bin").join("python")
    };
    if local.is_file() { local } else { PathBuf::from(if cfg!(windows) { "python" } else { "python3" }) }
}

fn start_bridge() -> Option<Child> {
    let root = project_root();
    let script = root.join("app").join("ui").join("desktop").join("bridge_server.py");
    let log_path = std::env::temp_dir().join("iskolar-python-bridge.log");
    if !script.exists() { eprintln!("Python bridge not found: {}", script.display()); return None; }
    let python = python_executable(&root);
    let mut command = Command::new(&python);
    command.arg("-u").arg(&script).current_dir(&root).stdin(Stdio::null());
    match OpenOptions::new().create(true).append(true).open(&log_path) {
        Ok(log) => {
            match log.try_clone() {
                Ok(stderr) => { command.stdout(Stdio::from(log)).stderr(Stdio::from(stderr)); }
                Err(error) => { eprintln!("Could not duplicate bridge log: {error}"); }
            }
        }
        Err(error) => { eprintln!("Could not open bridge log: {error}"); }
    }
    // A packaged Windows GUI has no console to show Python tracebacks.
    #[cfg(windows)]
    command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    match command.spawn() {
        Ok(child) => Some(child),
        Err(error) => {
            use std::io::Write;
            let message = format!("Could not start {}: {error}. Project: {}\n", python.display(), root.display());
            eprintln!("{message}");
            if let Ok(mut log) = OpenOptions::new().create(true).append(true).open(&log_path) {
                let _ = log.write_all(message.as_bytes());
            }
            None
        }
    }
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let child = start_bridge();
            app.manage(BridgeProcess(Mutex::new(child)));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.app_handle().try_state::<BridgeProcess>() {
                    if let Ok(mut child_slot) = state.0.lock() {
                        if let Some(mut child) = child_slot.take() { let _ = child.kill(); }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Iskolar ng Bayan desktop application");
}
