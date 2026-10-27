"""Launch the React/TypeScript desktop UI with the existing Python backend."""
import shutil
import subprocess
from pathlib import Path

def main():
    desktop = Path(__file__).resolve().parent / 'app' / 'ui' / 'desktop'
    npm = shutil.which('npm')
    if npm is None:
        raise SystemExit('Install Node.js and restart your terminal before launching the app.')
    if not (desktop / 'node_modules').exists():
        raise SystemExit('Run npm ci in app/ui/desktop first. See app/ui/desktop/README.md.')
    raise SystemExit(subprocess.call([npm, 'run', 'tauri', 'dev'], cwd=desktop))


if __name__ == "__main__":
    main()
