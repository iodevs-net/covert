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
        covert_cmd = str(base_dir / "Scripts" / "covert")
    else:
        pip_cmd = str(base_dir / "bin" / "pip")
        python_cmd = str(base_dir / "bin" / "python")
        covert_cmd = str(base_dir / "bin" / "covert")

    # Install covert-up from PyPI
    print("Installing covert-up from PyPI...")
    subprocess.check_call([pip_cmd, "install", "covert-up"])

    # Install an outdated package
    print("Installing outdated requests==2.28.0...")
    subprocess.check_call([pip_cmd, "install", "requests==2.28.0"])

    return python_cmd


def create_test_file(base_dir):
    test_file = base_dir / "test_script.py"
    with open(test_file, "w") as f:
        f.write("""
import requests
import sys

def test_requests():
    print(f"Requests version: {requests.__version__}")
    # Simple test: check if we can import and check version
    assert requests.__version__
    return True

if __name__ == "__main__":
    if test_requests():
        sys.exit(0)
    sys.exit(1)
""")
    return test_file


def run_covert_update(python_cmd, base_dir):
    print("\nRunning covert to update packages...")
    # Run covert as a module
    cmd = [python_cmd, "-m", "covert.cli"]

    # Set up environment with venv's bin in PATH
    env = os.environ.copy()
    if os.name == "nt":
        venv_bin = str(base_dir / "Scripts")
    else:
        venv_bin = str(base_dir / "bin")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")

    # We need to configure covert to run our test script
    # Since covert runs 'pytest' by default, we can pass a config or use flags if available,
    # but covert core logic runs a command.
    # Let's create a simple covert.toml in the test dir
    config_path = base_dir / "covert.toml"
    with open(config_path, "w") as f:
        f.write(f"""
[project]
name = "Test Project"
python_version = "3.12"

[testing]
enabled = true
command = "python3 test_script.py"
args = []

[updates]
strategy = "sequential"
version_policy = "latest"
""")

    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True, env=env)
    print("Covert Output:")
    print(result.stdout)
    if result.stderr:
        print("Covert Error:")
        print(result.stderr)
    return result.returncode


def verify_update(python_cmd):
    print("\nVerifying update...")
    result = subprocess.run(
        [python_cmd, "-c", "import requests; print(requests.__version__)"],
        capture_output=True,
        text=True,
    )
    version = result.stdout.strip()
    print(f"Current requests version: {version}")
    if version != "2.28.0":
        print("SUCCESS: Requests was updated!")
        return True
    else:
        print("FAILURE: Requests was NOT updated.")
        return False


def main():
    base_dir = Path("verification_sandbox").resolve()
    if base_dir.exists():
        import shutil

        shutil.rmtree(base_dir)

    python_cmd = setup_test_env(base_dir)
    create_test_file(base_dir)

    print(f"\nInitial State: requests==2.28.0")

    return_code = run_covert_update(python_cmd, base_dir)

    if return_code == 0:
        if verify_update(python_cmd):
            print("\n*** TEST PASSED: Safe update verification successful ***")
        else:
            print("\n*** TEST FAILED: Covert reported success but package not updated ***")
    else:
        print(f"\n*** TEST FAILED: Covert execution failed with code {return_code} ***")


if __name__ == "__main__":
    main()
