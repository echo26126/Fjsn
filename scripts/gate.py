
import subprocess
import sys
import os
import platform

def run_command(command, cwd=None, env=None):
    """Run a command and return the exit code."""
    print(f"Executing: {command} in {cwd or os.getcwd()}")
    
    # Use shell=True for flexibility with commands like 'npm'
    # On Windows, shell=True uses cmd.exe
    shell = True
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        return result.returncode
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1

def main():
    # Determine the root directory of the project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    # Use the current python executable
    python_exe = sys.executable

    print("="*60)
    print("STARTING AUTOMATED TEST GATE")
    print("="*60)

    # ---------------------------------------------------------
    # 1. Backend Smoke Tests
    # ---------------------------------------------------------
    print("\n[STEP 1] Running Backend Smoke Tests...")
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("[ERROR] pytest is not installed. Please run 'pip install -r backend/requirements.txt'")
        sys.exit(1)

    # Construct the command
    # Using python -m pytest is safer than just 'pytest'
    backend_cmd = f'"{python_exe}" -m pytest tests/test_smoke.py -v'
    
    backend_exit_code = run_command(backend_cmd, cwd=backend_dir)

    if backend_exit_code != 0:
        print("\n" + "!"*60)
        print("[FAILED] Backend Smoke Tests Failed!")
        print("!"*60)
        sys.exit(backend_exit_code)
    else:
        print("\n[PASSED] Backend Smoke Tests Passed!")

    # ---------------------------------------------------------
    # 2. Frontend E2E Tests
    # ---------------------------------------------------------
    print("\n[STEP 2] Running Frontend E2E Tests...")
    
    # Check if npm is available (simple check)
    npm_cmd = "npm"
    if platform.system() == "Windows":
        npm_cmd = "npm.cmd" 
        # Note: shell=True usually handles 'npm' -> 'npm.cmd' resolution, but being explicit is safer if not in shell
        # But with shell=True, 'npm' should work. Let's stick to 'npm' and let the shell resolve it.
        npm_cmd = "npm"

    # Construct the command
    # We use 'npm run test:e2e' which runs 'playwright test'
    frontend_cmd = f'{npm_cmd} run test:e2e'
    
    # Pass the current environment variables, but ensure CI=true so Playwright doesn't start in headed mode if not configured
    env = os.environ.copy()
    env["CI"] = "true" 

    frontend_exit_code = run_command(frontend_cmd, cwd=frontend_dir, env=env)

    if frontend_exit_code != 0:
        print("\n" + "!"*60)
        print("[FAILED] Frontend E2E Tests Failed!")
        print("Please ensure dependencies are installed: 'cd frontend && npm install && npx playwright install'")
        print("!"*60)
        sys.exit(frontend_exit_code)
    else:
        print("\n[PASSED] Frontend E2E Tests Passed!")

    print("\n" + "="*60)
    print("ALL TESTS PASSED - GATE CLEARED")
    print("="*60)

if __name__ == "__main__":
    main()
