#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    # Use installed project dependencies when launched with system Python.
    # Respect an explicitly activated virtual environment.
    if sys.prefix == sys.base_prefix:
        project_dir = Path(__file__).resolve().parent
        for environment in ('.venv', 'venv'):
            python_path = project_dir / environment / (
                'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
            )
            if python_path.is_file():
                sys.exit(subprocess.call([str(python_path), str(Path(__file__).resolve()), *sys.argv[1:]]))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulse_hms.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
