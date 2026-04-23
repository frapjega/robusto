import threading
import time
import os
import sys
import requests
import pyttsx3 as tts
import pyaudio
import json
import contextlib
from vosk import Model, KaldiRecognizer
from vision import vision  # importa la tua classe Vision con face_detection già modificata

# === Configurazione server ===
CONFIG_FILE = "config.txt"
PORT = 11434
MODEL_NAME = "robusto_mixtral_v7:latest"
chat_history = []

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
                             json=payload, timeout=30)
    response.raise_for_status()
    model_reply = response.json()["response"]
    chat_history.append({"role": "assistant", "content": model_reply})
    print("\n🧠 Risposta dal modello:\n")
    print(model_reply)
    return model_reply

# === THREAD PER VIDEOCAMERA ===
def run_camera():
    cam = vision()
    cam.run(face_detect=True, object_detect=False)

camera_thread = threading.Thread(target=run_camera)
camera_thread.daemon = True
camera_thread.start()

# === INIZIALIZZAZIONE MODALITA' VOCE ===
usa_voce = False
scelta = input("Vuoi che la AI risponda con la voce e ascolti la tua voce? (s/n): ").strip().lower()
if scelta == 's':
    usa_voce = True
    # TTS
    ita_voice_id = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_IT-IT_ELSA_11.0'
    engine = tts.init()
    engine.setProperty('voice', ita_voice_id)
    # ASR
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

# === CHIUSURA SE SERVER NON CONNETTE ===
if not check_server_connection():
    print("💡 Controlla che il server sia avviato e accessibile all'indirizzo specificato.")
    sys.exit()

# === LOOP PRINCIPALE ===
if usa_voce:
    print("🎤 Dì 'itis cardano' per attivare il sistema. Dì 'esci' per uscire.")
    # Hotword
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
    # Loop voce
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
else:
    # Loop testuale
    while True:
        PROMPT = input("🗣️ Scrivi il prompt da inviare a robusto: ").strip()
        if PROMPT in ["/esci", "exit", "esci", "/bye"]:
            print("👋 Fine della sessione.")
            time.sleep(1)
            break
        elif PROMPT == "/info":
            print("""Mixtral 8x7B – Specifiche Tecniche
Architettura: Sparse Mixture of Experts (SMoE)
Numero totale di parametri: 46,7 miliardi
Parametri attivi per token: 12,9 miliardi
Contesto massimo: 32.000 token
Lingue supportate: Inglese, francese, italiano, tedesco, spagnolo
Competenze principali: Generazione di codice, ragionamento matematico, comprensione multilingue
Prestazioni: Competitive con GPT-3.5 e LLaMA 2 70B
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
                s = input("è stato riscontrato un errore, riprovare? (s/n)").lower()
                if s == "s":
                    chat_request(PROMPT)
