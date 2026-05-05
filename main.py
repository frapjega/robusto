# Suppress TensorFlow/ABSL warnings before importing modules that use them
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow debug info
os.environ['ABSL_FLAGS_stderrthreshold'] = '2'  # Suppress ABSL warnings

import json
import queue
import sys
import threading
import logging

# Suppress absl logging
logging.getLogger('absl').setLevel(logging.ERROR)

import pyaudio
import pyttsx3
import vosk

import datetime


from vision.vision import Vision
from requests3 import ollama
from audio import run_tts, recognize_speech, capture_audio, text_queue


# to implement:
##  log -- da implementare write_log() dove serve
##  gestione camera -- done
##  gestione errori
##  comandi
##  scrittura su seriale


#create functions

def write_log(message):
    directory = "logs"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # In questo caso potresti volere un log giornaliero invece che al secondo
    day_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(directory, f"log-{day_str}.log")
    
    # Il file si chiude da solo alla fine del blocco 'with'
    with open(file_path, "a") as f:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")



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

def execute(par: int) -> None:
    print(f"eseguita azione: {ollama.movimenti[par]}")


def create_prompt(message, people):
    prompt = {"massage": message,
              "recognized people": people}
    prompt = str(prompt)
    # print(prompt)
    return prompt


def handle_loop():
    while True:
        try:
            prompt = input(">> ")
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
                        execute(index_movement)
                    except ValueError:
                        write_log(f"Movimento sconosciuto: {response['movement']}")
                        print(f"Avviso: Movimento non riconosciuto: {response['movement']}")
            except json.JSONDecodeError as e:
                write_log(f"Errore nel parsing della risposta: {e}")
                print(f"Avviso: Errore nel parsing della risposta")
        except KeyboardInterrupt:
            print("\nApplicazione terminata.")
            write_log("Applicazione terminata da utente")
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
                            execute(index_movement)
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
        print("Inizializzazione in corso...")
        write_log("Inizializzazione in corso")

        Ollama = ollama()
        vision = Vision()

        print("\nTelecamere disponibili:")
        cameras = vision.find_cameras()
        for cam_info in cameras:
            print(f"  • Indice {cam_info['index']}: {cam_info['name']}")
        
        cam = input("\nA quale camera vuoi connetterti? ")
        try:
            cam = int(cam)
            print(f"Connessione alla camera {cam}")
        except ValueError:
            print("Indice non valido. Inserisci un numero tra quelli indicati.")
            write_log("Errore: indice camera non valido")
            sys.exit(1)
            
        vision.start(camera=cam)
        
        audio = input("\nVuoi usare l'audio? (s/N): ").strip().lower()
        if audio == 's':
            print("Inizializzazione audio...")
            init_audio()
            handle_loop_audio()
        else:
            print("Modalità testo attiva\n")
            handle_loop()
    except KeyboardInterrupt:
        print("\nApplicazione terminata.")
        write_log("Applicazione terminata da utente durante inizializzazione")
    except Exception as e:
        print(f"Errore critico: {e}")
        write_log(f"Errore critico durante inizializzazione: {e}")
        sys.exit(1)