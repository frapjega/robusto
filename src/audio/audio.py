#!/usr/bin/env python3
"""
local_voice.py
──────────────
Real-time Speech Recognition + Text-to-Speech interamente in locale.

STT : Vosk  (offline, KaldiRecognizer)
TTS : pyttsx3  (espeak-ng su Linux)

Dipendenze sistema:
    sudo apt install portaudio19-dev espeak-ng

Dipendenze Python (Python 3.12):
    pip install vosk pyaudio pyttsx3

Modello Vosk (scegli la lingua):
    https://alphacephei.com/vosk/models
    Scarica e decomprimi nella stessa cartella → rinomina in "model/"
    Esempio italiano: vosk-model-small-it-0.22
"""

import json
import queue
import sys
import threading

import pyaudio
import pyttsx3
import vosk

# ┌─────────────────────────────────────────────────────────────┐
# │                      CONFIGURAZIONE                         │
# └─────────────────────────────────────────────────────────────┘

MODEL_PATH  = "model"   # Cartella del modello Vosk scaricato
SAMPLE_RATE = 16_000    # Hz — Vosk richiede 16kHz
CHUNK_SIZE  = 4_096     # Byte per chunk audio (~0.13s a 16kHz/16bit)
TTS_RATE    = 160       # Parole al minuto per il TTS
TTS_VOLUME  = 1.0       # Volume TTS (0.0 – 1.0)


# ┌─────────────────────────────────────────────────────────────┐
# │                         CODE                                │
# └─────────────────────────────────────────────────────────────┘

# Due code thread-safe che collegano i tre stadi della pipeline:
#   [microfono] → audio_queue → [Vosk STT] → text_queue → [TTS]
audio_queue: queue.Queue[bytes] = queue.Queue()
text_queue:  queue.Queue[str]   = queue.Queue()


# ── STADIO 1: Cattura audio dal microfono ──────────────────────

def capture_audio(stream: pyaudio.Stream, stop: threading.Event) -> None:
    """
    Thread dedicato alla cattura audio.

    Legge continuamente CHUNK_SIZE byte dal microfono tramite PyAudio
    e li inserisce in audio_queue. Usa exception_on_overflow=False per
    non crashare se il buffer si riempie (es. CPU carica).

    Parametri
    ---------
    stream : pyaudio.Stream  — stream audio già aperto
    stop   : threading.Event — segnale per terminare il loop
    """
    while not stop.is_set():
        try:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_queue.put(data)
        except OSError as exc:
            # Errore hardware (disconnessione mic, ecc.)
            print(f"[AudioCapture] Errore: {exc}", file=sys.stderr)
            stop.set()          # ferma tutto il programma
            break


# ── STADIO 2: Riconoscimento vocale con Vosk ──────────────────

def recognize_speech(model_path: str, stop: threading.Event) -> None:
    """
    Thread dedicato allo Speech-To-Text.

    Carica il modello Vosk una sola volta, poi entra in loop:
      • AcceptWaveform() → True  : frase completata → manda il testo a text_queue
      • AcceptWaveform() → False : risultato parziale → mostra in-place su stdout

    Vosk usa un riconoscitore Kaldi ottimizzato: nessuna connessione a internet,
    latenza molto bassa, funziona su CPU senza GPU.

    Parametri
    ---------
    model_path : str              — percorso alla cartella del modello
    stop       : threading.Event  — segnale per terminare il loop
    """
    print("[STT] Caricamento modello Vosk...", flush=True)
    model = vosk.Model(model_path)
    rec   = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    print("[STT] Modello caricato. In ascolto...\n", flush=True)

    while not stop.is_set():
        # .get(timeout=…) evita il blocco infinito: ogni 0.5s
        # controlla se stop è stato impostato.
        try:
            data = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if rec.AcceptWaveform(data):
            # ── Risultato finale (fine frase) ──
            result = json.loads(rec.Result())
            text   = result.get("text", "").strip()
            if text:
                # Vai a capo per sovrascrivere l'eventuale partial
                print(f"\r[Tu] {text}                    ", flush=True)
                text_queue.put(text)        # → TTS
        else:
            # ── Risultato parziale (frase in corso) ──
            partial = json.loads(rec.PartialResult())
            partial_text = partial.get("partial", "").strip()
            if partial_text:
                # \r sovrascrive la riga → effetto "live"
                print(f"\r[...] {partial_text}    ", end="", flush=True)


# ── STADIO 3: Sintesi vocale con pyttsx3 ──────────────────────

def run_tts(engine: pyttsx3.Engine, stop: threading.Event, text: str = None) -> None:
    """
    Loop TTS che gira sul thread PRINCIPALE.

    pyttsx3 su Linux usa il backend espeak-ng, che internamente
    gestisce un driver audio proprio. Su alcuni sistemi crasha se
    chiamato da un thread secondario, quindi lo eseguiamo sul main.

    Legge il testo da text_queue e lo riproduce vocalmente.

    Parametri
    ---------
    engine : pyttsx3.Engine   — motore TTS già inizializzato
    stop   : threading.Event  — segnale per terminare il loop
    text   : stringa   — testo da sintetizzare
    """
    while not stop.is_set():
        if text is None:
            try:
                text = text_queue.get(timeout=0.5)
            except queue.Empty:
                continue

        print(f"[TTS] → {text}", flush=True)
        engine.say(text)
        engine.runAndWait()     # blocca finché la frase non è riprodotta


# ── MAIN ──────────────────────────────────────────────────────

def main() -> None:
    # 1. Inizializza il motore TTS
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

    print("Premi Ctrl+C per uscire.\n")

    try:
        # Il TTS gira sul main thread (motivo: compatibilità espeak-ng)
        run_tts(engine, stop_event)
    except KeyboardInterrupt:
        print("\n[INFO] Interruzione ricevuta. Chiusura...")
    finally:
        stop_event.set()            # segnala ai thread di fermarsi
        t_capture.join(timeout=2)
        t_stt.join(timeout=2)
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print("[INFO] Chiusura completata.")


if __name__ == "__main__":
    main()