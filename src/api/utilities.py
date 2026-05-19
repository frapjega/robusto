# import os
import datetime
import os
from pathlib import Path
import platform
import subprocess

from ..log.log import write_log



def ping(host):
    # 'nt' indica Windows, altrimenti assume Linux/POSIX
    if platform.system() == "Windows":
        command = ['ping', '-n', '1', '-w', '1000', host]
    elif platform.system() == "Darwin":  # macOS
        command = ['ping', '-W', '1000', '-c', '1', host]
    else:  # Linux
        command = ['ping', '-W', '1', '-c', '1', host]
    try:
        # Esegue il comando nascondendo l'output
        subprocess.run(
            command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            check=True
        )

        write_log(f"ping to {host}, host reachable")
        return True
    except:
        write_log(f"ping to {host}, unpossible to reach destination")
        return False
