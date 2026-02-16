import os
import subprocess
import sys
import venv
from pathlib import Path


def setup_test_env(base_dir):
    print(f"Creating test environment in {base_dir}...")
    venv.create(base_dir, with_pip=True)

    if os.name == "nt":
        pip_cmd = str(base_dir / "Scripts" / "pip")
        python_cmd = str(base_dir / "Scripts" / "python")
    else:
        pip_cmd = str(base_dir / "bin" / "pip")
        python_cmd = str(base_dir / "bin" / "python")

    # Install covert-up from PyPI
    print("Installing covert-up from PyPI...")
    subprocess.check_call([pip_cmd, "install", "covert-up"])

    # Install an outdated package
    print("Installing outdated requests==2.28.0...")
    subprocess.check_call([pip_cmd, "install", "requests==2.28.0"])

    return python_cmd


def create_breaking_test_file(base_dir):
    test_file = base_dir / "test_breaking.py"
    with open(test_file, "w") as f:
        f.write("""
import requests
import sys

def test_api_compatibility():
    print(f"Current requests version: {requests.__version__}")
    # Simulating a breaking change: 
    # This test ONLY passes if version is exactly 2.28.0
    # Any update will cause this test to fail, triggering rollback
    if requests.__version__ != "2.28.0":
        print("ERROR: Version mismatch! This app requires exactly requests==2.28.0")
        return False
    return True

if __name__ == "__main__":
    if test_api_compatibility():
        sys.exit(0)
    sys.exit(1)
""")
    return test_file


def run_covert_update(python_cmd, base_dir):
    print("\nRunning covert to update packages...")
    # Run covert as a module with explicit config and verbose logging
    cmd = [python_cmd, "-m", "covert.cli", "-c", "covert.toml", "-v"]

    # Set up environment with venv's bin in PATH
    env = os.environ.copy()
    if os.name == "nt":
        venv_bin = str(base_dir / "Scripts")
    else:
        venv_bin = str(base_dir / "bin")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")

    # Configure covert to run our breaking test script
    config_path = base_dir / "covert.toml"
    with open(config_path, "w") as f:
        f.write(f"""
[project]
name = "Breaking Project"
python_version = "3.12"

[testing]
enabled = true
command = "python"
args = ["test_breaking.py"]

[updates]
strategy = "sequential"
version_policy = "latest"
""")

    # We expect covert to fail the update but succeed in restoring the old version
    # So covert itself might return a non-zero exit code or zero depending on implementation
    # But for us, the important thing is the final state of the package
    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True, env=env)
    print("Covert Output:")
    print(result.stdout)
    if result.stderr:
        print("Covert Error:")
        print(result.stderr)
    return result.returncode


def verify_rollback(python_cmd):
    print("\nVerifying rollback...")
    result = subprocess.run(
        [python_cmd, "-c", "import requests; print(requests.__version__)"],
        capture_output=True,
        text=True,
    )
    version = result.stdout.strip()
    print(f"Current requests version: {version}")

    if version == "2.28.0":
        print("SUCCESS: Rollback successful! Version is back to 2.28.0.")
        return True
    else:
        print(f"FAILURE: Rollback failed. Version is {version}.")
        return False


def main():
    base_dir = Path("rollback_sandbox").resolve()
    if base_dir.exists():
        import shutil

        shutil.rmtree(base_dir)

    python_cmd = setup_test_env(base_dir)
    create_breaking_test_file(base_dir)

    print(f"\nInitial State: requests==2.28.0")

    # We run covert. It should try to update, fail the test, and rollback.
    run_covert_update(python_cmd, base_dir)

    if verify_rollback(python_cmd):
        print("\n*** TEST PASSED: Rollback verification successful ***")
    else:
        print("\n*** TEST FAILED: Rollback verification failed ***")


if __name__ == "__main__":
    main()
