import subprocess
import re
from datetime import datetime
from typing import List, Dict, Optional

import RPi.GPIO as GPIO

def lister_connexions_ssh() -> List[Dict[str, str]]:
    lines = subprocess.check_output('who', text=True).splitlines()
    return [re.match(r'^(\w+)\s+(pts/\d+)\s+(.+?)\s+\((.+)\)$', line).groups()
            for line in lines if 'pts/' in line and '(' in line]

def get_pid_pts(id: int=1) -> Optional[int]:
    result = subprocess.run(['bash', '-c', f'ps aux | grep "pts/{id}"'], 
                        capture_output=True, text=True, check=True)

    for line in result.stdout.split('\n'):
        if 'grep' not in line and 'sshd' in line and line.strip():
            pid = int(line.split()[1])
            return pid
    return None

# Exemple d'utilisation
if __name__ == "__main__":
    print(lister_connexions_ssh())
    print(get_pid_pts(0))
