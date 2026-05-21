# Suppress TensorFlow/ABSL warnings before importing modules that use them
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow debug info
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Disable oneDNN custom op warnings
os.environ['ABSL_FLAGS_stderrthreshold'] = '2'  # Suppress ABSL warnings
os.environ['ABSL_LOG_CPP_MIN_LEVEL'] = '3'  # Suppress absl C++ logs
import serial.tools.list_ports

import traceback
import json
import queue
import sys
import threading
import logging
from pathlib import Path
import datetime
import time

# Classe che duplica stderr su file LOG e terminale
logs_dir = Path(__file__).resolve().parent / "logs"
logs_dir.mkdir(exist_ok=True)
day_str = datetime.datetime.now().strftime("%Y-%m-%d")
stderr_file = logs_dir / f"log-{day_str}.log"
stderr_fd = os.open(str(stderr_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
os.dup2(stderr_fd, 2)  # Reindirizza file descriptor 2 (stderr)

# Suppress absl logging
logging.getLogger('absl').setLevel(logging.ERROR)

import pyaudio
import pyttsx3
import vosk


from src.vision.vision import Vision
from src.api.requests3 import ollama, Ollama
from src.audio.audio import run_tts, recognize_speech, capture_audio, text_queue

from src.log.log import write_log
from src.api.utilities import ping


# to implement:
##  log -- da implementare write_log() dove serve
##  gestione camera -- done
##  gestione errori
##  comandi
##  scrittura su seriale

SerPort = None
SerBaud = 9600

def execute_movement(par: int) -> None:

    if par >= 0 and par < 14:

        try:
            #with serial.Serial(SerPort, SerBaud, timeout=1) as ser:
            with serial.Serial("COM3", "9600", timeout=1) as ser:
                
                time.sleep(2)
                ser.write(str(par).encode('utf-8'))
            print(f"eseguita azione: {ollama.movimenti[par]}, scritto {par}")

        except Exception as e:
            if str(e) == "invalid literal for int() with base 10: ''":
                #from rich import print

                #print(f"[bold red]Nessuna porta seriale inserita, impossibile inviare movimento \"{ollama.movimenti[par]}\"[/bold red].")
                print(f"Nessuna porta seriale inserita, impossibile inviare movimento \"{ollama.movimenti[par]}\".")
                write_log(f"nessuna porta seriale inserita, non eseguito movimento {ollama.movimenti[par]}")
            else:
                print(f"errore durante esecuzione ezione: {e}")
                write_log(f"errore durante esecuzione ezione: {e}")
            


        ### da completare

        write_log(f"executed movement {par}: {ollama.movimenti[par]}")

    else:
        write_log(f"impossible execute movemnt {par} (it doesn't exist)")



def execute_command(input: str):

    write_log(f"recived command{input}")


    command = input.split()[0]
    try:
        par = input.split()[1]
    except IndexError:
        par = None
    try:
        flag = input.split()[2]
    except:
        flag = None


    if command == "/execute":
        if par is None:
            print("""comando /execute deve essere seguito da un numero intero 0-12""")
            
        else:
            try:
                par = int(par)
                if par > 12 or par < 0:
                    raise ValueError
                execute_movement(par)
                print("movimento eseguito con successo")
                
            except:
                print("""comando /execute deve essere seguito da un numero intero 0-12""")
                


    elif command == "/setIP":
        if par is not None:
            success, result = Ollama.change_conf(IP_ollama=par)
            if success:
                print("modifica IP server avvenuta con successo")
            elif ping(par):
                print("assicurarsi che ollama sia in esecuzione sul server")
            else:
                print("controllare lo stato del server")
        else:
            print(f"comando \"{command}\" deve essere seguito dall'indirizzo IP del server")

        

    elif command == "/setModel":
        success, _ = Ollama.change_conf(model=par)
        if success:
            print("cambio modello avvento con successo")
            
        else:
            print("impossibile modificare il modello, controlla lo stato del server ed i modelli presenti")
            

    elif command == "/seeModel":
        success, models = Ollama.see_model()
        if success:
            if models:
                print("modelli disponibili:")
                for model in models:
                    print(model)
            else:
                print("nessun modello presente sul server")
        else:
            print("errore nell'interrogazione del server")

    elif command == "/help":
        print("""
Comandi disponibili:
    /execute [0-12]     Esegue un movimento specifico (richiede un numero intero da 0 a 12).
    /setIP [IP]         Cambia l'indirizzo IP del server Ollama.
    /setModel [nome]    Imposta il modello linguistico da utilizzare sul server.
    /seeModel           Mostra l'elenco dei modelli disponibili sul server.
    /help               Mostra questo messaggio di aiuto.
""")
        

    else:
        print(f"comando \"{command}\" non riconosciuto")
        write_log(f"commad \'{command}\' not known")
        print("scrivi /help per vedere elenco comandi")


def init_audio():

    MODEL_PATH  = "model"   # Cartella del modello Vosk scaricato
    SAMPLE_RATE = 16_000    # Hz — Vosk richiede 16kHz
    CHUNK_SIZE  = 4_096     # Byte per chunk audio (~0.13s a 16kHz/16bit)
    TTS_RATE    = 160       # Parole al minuto per il TTS
    TTS_VOLUME  = 1.0       # Volume TTS (0.0 – 1.0)

    # 1. Inizializza il motore TTS
    global engine 
    engine = pyttsx3.init()
    engine.setProperty("rate",   TTS_RATE)
    engine.setProperty("volume", TTS_VOLUME)

    # Opzionale: elenca le voci disponibili e scegli quella italiana
    # voices = engine.getProperty("voices")
    # for v in voices: print(v.id)
    # engine.setProperty("voice", "it")   # codice lingua espeak-ng

    # 2. Apri lo stream audio dal microfono
    pa     = pyaudio.PyAudio()
    stream = pa.open(
        format           = pyaudio.paInt16,   # 16 bit interi (richiesto da Vosk)
        channels         = 1,                 # mono
        rate             = SAMPLE_RATE,       # 16000 Hz
        input            = True,
        frames_per_buffer= CHUNK_SIZE,
    )

    # 3. Evento condiviso per shutdown ordinato
    global stop_event
    stop_event = threading.Event()

    # 4. Avvia i thread in background (daemon=True → muoiono col main)
    t_capture = threading.Thread(
        target  = capture_audio,
        args    = (stream, stop_event),
        daemon  = True,
        name    = "AudioCapture",
    )
    t_stt = threading.Thread(
        target  = recognize_speech,
        args    = (MODEL_PATH, stop_event),
        daemon  = True,
        name    = "STT",
    )

    t_capture.start()
    t_stt.start()
    write_log("inizialized audio")



def create_prompt(message, people):
    prompt = {"message": message,
              "recognized people": people}
    prompt = str(prompt)
    write_log(f"created prompt: \"{prompt}\"")
    # print(prompt)
    return prompt


def handle_loop():
    while True:
        try:
            print(">> ", end=" ", flush=True)
            prompt = input("")
            if not prompt.strip():
                continue
            if prompt.strip().startswith("/"):
                execute_command(prompt)
                continue
            try:                
                prompt = create_prompt(prompt, vision.get_last_recognized())
            except Exception as e:
                write_log(f"Errore nella creazione del prompt: {e}")
                prompt = create_prompt(prompt, None)
                
            response = Ollama.request(prompt)
            
            try:
                response = json.loads(response) 

                # da implementare se modello assenste
                print(f"AI: {response.get('response', 'Errore nella risposta')}")
                
                if "movement" in response:
                    try:
                        index_movement = Ollama.movimenti.index(response["movement"])
                        execute_movement(index_movement)
                    except ValueError:
                        write_log(f"Movimento sconosciuto: {response['movement']}")
                        print(f"Avviso: Movimento non riconosciuto: {response['movement']}")
            except json.JSONDecodeError as e:
                write_log(f"Errore nel parsing della risposta: {e}")
                print(f"Avviso: Errore nel parsing della risposta")
        except KeyboardInterrupt:
            print("\nApplicazione terminata.")
            write_log("Applicazione terminata da utente")
            write_log("")
            write_log("========== END EXECUTION ==========")
            write_log("")
            write_log("")

            break
        except Exception as e:
            write_log(f"Errore non previsto in handle_loop: {e}")
            print(f"Errore: {e}")



def handle_loop_audio():
    try:
        while True:
            try:
                prompt = text_queue.get(timeout=0.5)
            except queue.Empty:
                prompt = None
            
            if prompt is not None:
                try:                
                    prompt = create_prompt(prompt, vision.get_last_recognized())
                except Exception as e:
                    write_log(f"Errore nella creazione del prompt: {e}")
                    prompt = create_prompt(prompt, None)
                    
                response = Ollama.request(prompt)
                
                try:
                    response = json.loads(response) 
                    print(f"AI: {response.get('response', 'Errore nella risposta')}")
                    
                    if "movement" in response:
                        try:
                            index_movement = Ollama.movimenti.index(response["movement"])
                            execute_movement(index_movement)
                            run_tts(engine, stop_event, response["response"])
                        except ValueError:
                            write_log(f"Movimento sconosciuto: {response['movement']}")
                            print(f"Avviso: Movimento non riconosciuto: {response['movement']}")
                except json.JSONDecodeError as e:
                    write_log(f"Errore nel parsing della risposta: {e}")
                    print(f"Avviso: Errore nel parsing della risposta")
    except KeyboardInterrupt:
        print("\nApplicazione terminata.")
        write_log("Applicazione terminata da utente")
    except Exception as e:
        write_log(f"Errore non previsto in handle_loop_audio: {e}")
        print(f"Errore: {e}")




if __name__ == "__main__":
    try:
        
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Nasconde info e warning
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Disattiva il warning specifico su oneDNN
        os.environ['ABSL_LOG_CPP_MIN_LEVEL'] = '0'

        print("Inizializzazione in corso...")
        write_log("Inizializzazione in corso")


        vision = Vision()

        _, models = Ollama.see_model()
        if _:
            print(f"scegli modello:")
            for i in models:
                print("    "+i)
            Ollama.change_model(input())


        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"Porta: {port.device} - Descrizione: {port.description}")
        print("\nA quale porta vuoi collegarti?", end=" ", flush=True)
        port = input("")
        SerPort = port
        print("\nInserisci il baud rate (default 9600)", end=" ", flush=True)
        baud = input("")
        if baud == None:
            baud = 9600

        SerBaud = baud

        


        print("\nTelecamere disponibili:")
        cameras = vision.find_cameras()
        for cam_info in cameras:
            print(f"  • {cam_info['index']}: {cam_info['name']}")
        
        print("\nA quale camera vuoi connetterti?", end=" ", flush=True)
        cam = input("")

        try:
            cam = int(cam)
            print(f"Connessione alla camera {cam}")
        except ValueError:
            print("Indice non valido. Inserisci un numero tra quelli indicati.")
            write_log(f"Errore: indice camera non valido, inserito: {cam}")
            sys.exit(1)
            
        vision.start(camera=cam)
        
        # audio = input("\nVuoi usare l'audio? (s/N): ").strip().lower()
        # if audio == 's':
        #     print("Inizializzazione audio...")
        #     init_audio()
        #     handle_loop_audio()
        # else:
        #     print("Modalità testo attiva\n")
        #     handle_loop()


        handle_loop()
    except KeyboardInterrupt:
        print("\nApplicazione terminata.")
        write_log("Applicazione terminata da utente durante inizializzazione")
        write_log("")
        write_log("========== END EXECUTION ==========")
        write_log("")
        write_log("")
    except Exception as e:
        print(f"Errore critico: {e}")
        write_log(f"Errore critico durante inizializzazione: {e} {traceback.format_exc()}")
        sys.exit(1)