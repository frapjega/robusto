import json
import queue
import sys
import threading

import pyaudio
import pyttsx3
import vosk


from vision.vision import Vision
from requests3 import ollama
from audio import run_tts, recognize_speech, capture_audio, text_queue


# to implement:
##  gestione camera
##  gestione errori
##  comandi
##  scrittura su seriale


#create objects

Ollama = ollama()
vision = Vision()


#create functions

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

        prompt = input(">> ")
        try:                
            prompt = create_prompt(prompt, vision.get_last_recognized())
        except:
            prompt = create_prompt(prompt, None)
            
        response = Ollama.request(prompt)
        
        try:
            response = json.loads(response) 
            # print(response)    
            print(f"AI: {response["response"]}")    
            # print(response["movement"])    
        except:
            print(response)    

        index_movement = Ollama.movimenti.index(response["movement"])
        execute(index_movement)



def handle_loop_audio():
    while True:

        try:
            prompt = text_queue.get(timeout=0.5)
        except:
            prompt = None
        
        if prompt is not None:
            try:                
                prompt = create_prompt(prompt, vision.get_last_recognized())
            except:
                prompt = create_prompt(prompt, None)
                
            response = Ollama.request(prompt)
            
            try:
                response = json.loads(response) 
                # print(response)    
                print(f"AI: {response["response"]}")
                # print(response["movement"])    
            except:
                print(response)    

            index_movement = Ollama.movimenti.index(response["movement"])
            execute(index_movement)
            run_tts(engine, stop_event, response["response"])
        else:
            print(":<>")




if __name__ == "__main__":
    print("inizializzazione in corso...")
    audio = input("vuoi usare l'audio? (s/N)").strip().lower()
    if audio == 's':
        init_audio()
        handle_loop_audio()
    else:
        handle_loop()