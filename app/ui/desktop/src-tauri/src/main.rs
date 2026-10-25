#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{path::PathBuf, process::{Child, Command, Stdio}, sync::Mutex};
use tauri::Manager;

struct BridgeProcess(Mutex<Option<Child>>);

fn project_root() -> PathBuf {
    // src-tauri -> desktop -> ui -> app -> project root
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../").canonicalize().unwrap_or_else(|_| PathBuf::from("."))
}

fn start_bridge() -> Option<Child> {
    let root = project_root();
    let script = root.join("app").join("ui").join("desktop").join("bridge_server.py");
    if !script.exists() { eprintln!("Python bridge not found: {}", script.display()); return None; }
    let python = if cfg!(windows) { "python" } else { "python3" };
    match Command::new(python).arg(&script).current_dir(root).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::inherit()).spawn() {
        Ok(child) => Some(child),
        Err(error) => { eprintln!("Could not start Python bridge: {error}. Start it manually with python app/ui/desktop/bridge_server.py"); None }
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
