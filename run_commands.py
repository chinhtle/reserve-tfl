import subprocess
import os 

def run_command(command):
    try:
        result = subprocess.run(command,shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing command: ", e)
        print(e.stderr)
        
venv_dir = "venv"
if not os.path.exists(venv_dir):
    run_command(f"python -m venv {venv_dir}")
else:
    print(f"The virual environment {venv_dir} already exists")

requirements_file = "requirements.txt"
if os.path.exists(requirements_file):
    run_command(f"{venv_dir}\\Scripts\\python.exe -m pip install --upgrade pip")
    run_command(f"{venv_dir}\\Scripts\\pip.exe install -r {requirements_file}")
else:
    print("No requirements.txt found")
    
script_name = "reserve_tfl.py"
if os.path.exsts(script_name):
    run_command(f"{venv_dir}\\Scripts\\python.exe {script_name}")
else:
    print(f"{script_name} does not exist. Please check the filename and try again.")
    