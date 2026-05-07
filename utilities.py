import os
import datetime
import os
from pathlib import Path




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

