# import os
import datetime
import os
from pathlib import Path
import platform
import subprocess


def write_log(message):
    
    directory = str((Path(__file__).resolve().parent / "logs").resolve())
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # In questo caso potresti volere un log giornaliero invece che al secondo
    day_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(directory, f"log-{day_str}.log")
    
    # Il file si chiude da solo alla fine del blocco 'with'
    with open(file_path, "a") as f:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

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
