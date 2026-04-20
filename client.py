# made by: Guido Gusberti, Alex Vadeu, Pietro Fratesi ITIS Cardano 2025

import os
import sys
import time
import json
import requests
import pyttsx3 as tts
import pyaudio
from vosk import Model, KaldiRecognizer
import contextlib


# === Configurazione file e modello ===

CONFIG_FILE = "config.txt"
PORT = 11434
MODEL_NAME = "robusto_mixtral_v7:latest" # "mixtral:8x7b"#

chat_history = []


# === Funzioni IP/config ===

def carica_ip():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    else:
        return "10.110.99.5"



def salva_ip(nuovo_ip):
    with open(CONFIG_FILE, "w") as f:
        f.write(nuovo_ip)


SERVER_IP = carica_ip()


# === Funzione per testare la connessione al server ===

def check_server_connection():
    try:
        url = f"http://{SERVER_IP}:{PORT}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print("✅ Connessione al server riuscita.\n")
            return True
        else:
            print(f"⚠️ Server risponde con codice: {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        print("❌ Impossibile connettersi al server:")
        print(e)
        return False


# === Funzione di invio al modello + gestione storico ===

def chat_request(prompt: str) -> str:
    global chat_history
    chat_history.append({"role": "user", "content": prompt})
    full_prompt = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history)

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(f"http://{SERVER_IP}:{PORT}/api/generate",
                             json=payload,
                             timeout=30)

    response.raise_for_status()
    model_reply = response.json()["response"]

    #model_reply = response.json()

    print("\n🧠 Risposta dal modello:\n")
    print(model_reply)
    chat_history.append({"role": "assistant", "content": model_reply})
    return model_reply



# === Interfaccia iniziale ===

check_server_connection()
print("""

██╗████████╗██╗███████╗                                    
██║╚══██╔══╝██║██╔════╝                                    
██║   ██║   ██║███████╗                                    
██║   ██║   ██║╚════██║                                    
██║   ██║   ██║███████║                                    
╚═╝   ╚═╝   ╚═╝╚══════╝                                    
 ██████╗ █████╗ ██████╗ ██████╗  █████╗ ███╗   ██╗ ██████╗ 
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔═══██╗
██║     ███████║██████╔╝██║  ██║███████║██╔██╗ ██║██║   ██║
██║     ██╔══██║██╔══██╗██║  ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╗██║  ██║██║  ██║██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 

""", end='\n\n')



print('''COME UTILIZZARE IL MODELLO:
    - scrivi le tue domande 
    - leggi le tue risposte 
    - per smettere scrivi "esci"
    - per avere informazioni dettagliate sul modello scrivi "/info"
    - per verificare la connessione scrivi "/ping"
    - per cambiare l'IP del server scrivi "/cambia_ip"
''', end='\n\n')



# === Scelta modalità ===

usa_voce = False
scelta = input("Vuoi che la AI risponda con la voce e ascolti la tua voce? (s/n): ").strip().lower()

if scelta == 's':
    usa_voce = True
    # Inizializza TTS
    ita_voice_id = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_IT-IT_ELSA_11.0'
    engine = tts.init()
    engine.setProperty('voice', ita_voice_id)

    # Prepara ASR
    MODEL_PATH = "vosk-model-it-0.22"
    RATE = 16000
    CHUNK = 1024
    SILENCE_TIME = 1

    @contextlib.contextmanager

    def suppress_stdout_stderr():
        old_out = os.dup(1); old_err = os.dup(2)

        with open(os.devnull, "w") as fnull:
            os.dup2(fnull.fileno(), 1); os.dup2(fnull.fileno(), 2)
            try: yield
            finally:
                os.dup2(old_out, 1); os.dup2(old_err, 2)

    with suppress_stdout_stderr():
        vosk_model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(vosk_model, RATE)

    pa = pyaudio.PyAudio()

    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE,

                     input=True, frames_per_buffer=CHUNK)


# === Chiusura se non connette ===

if not check_server_connection():
    print("💡 Controlla che il server sia avviato e accessibile all'indirizzo specificato.")
    sys.exit()


# === FLOW VOCE ===

if usa_voce:
    print("🎤 Dì 'itis cardano' per attivare il sistema. Dì 'esci' per uscire.")
    # Attivazione hotword

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            text = json.loads(recognizer.Result()).get("text", "").lower()
            if "itis cardano" in text:
                print("✅ Sistema attivato!")
                break

            if "esci" in text:
                print("👋 Uscita dal programma.")
                stream.stop_stream(); stream.close(); pa.terminate()
                sys.exit()

    # Loop principale voce

    while True:
        frames = []
        print("\n🎧 In ascolto...")
        last_time = None; recording = False; final_txt = ""

        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                text = json.loads(recognizer.Result()).get("text", "").strip()
                if text:
                    frames.append(data); last_time = time.time()
                    recording = True; final_txt = text
                if "esci" in text:
                    print("👋 Uscita dal programma.")
                    stream.stop_stream(); stream.close(); pa.terminate()
                    sys.exit()

            if recording and last_time and (time.time() - last_time > SILENCE_TIME):
                break

        if final_txt:
            print(final_txt + "\n")
            reply = chat_request(final_txt)
            engine.say(reply)
            engine.runAndWait()


# === FLOW TESTO ===

else:
    while True:
        PROMPT = input("🗣️ Scrivi il prompt da inviare a robusto: ").strip()
        if PROMPT in ["/esci", "exit", "esci", "/bye"]:
            print("👋 Fine della sessione.")
            time.sleep(1)
            break

        elif PROMPT == "/info":
            print("""
Mixtral 8x7B – Specifiche Tecniche
Architettura: Sparse Mixture of Experts (SMoE)
Numero totale di parametri: 46,7 miliardi
Parametri attivi per token: 12,9 miliardi (2 esperti attivi su 8 per ciascun token)
Contesto massimo: 32.000 token
Lingue supportate: Inglese, francese, italiano, tedesco, spagnolo
Competenze principali: Generazione di codice, ragionamento matematico, comprensione multilingue
Prestazioni: Competitive con GPT-3.5 e LLaMA 2 70B su benchmark comuni
Versione instruct: Ottimizzata per seguire istruzioni; punteggio MT-Bench: 8,3
Licenza: Apache 2.0 (open source, uso commerciale consentito)
Efficienza: Paragonabile in velocità a un modello denso da 12B parametri
""")

        elif PROMPT == "/ping":
            check_server_connection()

        elif PROMPT == "/cambia_ip":
            nuovo_ip = input("🔧 Inserisci il nuovo IP del server: ").strip()
            salva_ip(nuovo_ip)
            SERVER_IP = nuovo_ip
            print(f"✅ IP cambiato con successo in {SERVER_IP}.")

            if not check_server_connection():
                print("⚠️ Connessione non riuscita con il nuovo IP.")

        else:
            try:
                chat_request(PROMPT)
            except:
                s = input("è stato riscontrato un errore, riptovare? (s/n)").lower()
                if s == "s":
                    chat_request(PROMPT)
