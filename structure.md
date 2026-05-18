# Struttura del codice di Robusto

Questo progetto è organizzato attorno a tre aree principali:
- `main.py` — Entrypoint dell’applicazione, interazione con l’utente, gestione della telecamera e del ciclo di elaborazione delle richieste.
- `utilities.py` — Infrastruttura di logging e funzioni di utilità comuni.
- `requests3.py` — Client per l’interazione con il server Ollama/GPT e gestione dei modelli.
- `audio.py` — Pipeline locale per cattura audio, riconoscimento vocale e sintesi vocale.
- `vision/vision.py` — Modulo di visione artificiale basato su DeepFace per riconoscimento facciale e gestione camera.
- `logs/` — Cartella dove vengono salvati i log giornalieri.

## Panoramica dei moduli

### `main.py`
È il cuore dell’applicazione.
- Configura il logging con `utilities.setup_logging()`.
- Carica le dipendenze principali: `Vision`, `Ollama`, audio e utilità di log.
- Gestisce l’inizializzazione dell’applicazione:
  - lettura dei modelli Ollama,
  - selezione della porta seriale,
  - selezione della telecamera.
- Fornisce il ciclo testuale in cui l’utente inserisce comandi o messaggi.
- Converte il testo dell’utente in prompt strutturati con `create_prompt()`.
- Invia i prompt a Ollama e processa la risposta AI, incluso il movimento da eseguire.
- Registra gli eventi nel file di log tramite `write_log()`.

### `utilities.py`
Contiene le funzioni di supporto condivise.
- `setup_logging()` crea un logger centralizzato con output su file giornaliero e su console.
- `write_log()` consente ai moduli di registrare messaggi con livelli di dettaglio (`info`, `warning`, `error`).
- `ping()` verifica la raggiungibilità di un host e annota il risultato nei log.

### `requests3.py`
Implementa il client Ollama, il server di AI locale.
- Definisce la classe `ollama` con:
  - `change_conf()` — modifica IP, porta e modello e verifica la connessione.
  - `check_IP()` — controlla lo stato del server.
  - `request()` — invia una richiesta di chat con formato JSON specifico e registra il payload e la risposta.
  - `change_model()` — cambia il modello usato, controllando prima i modelli disponibili.
  - `see_model()` — recupera la lista dei modelli installati sul server.
- Conserva lo storico delle conversazioni in `self.history`.
- Definisce l’elenco dei movimenti disponibili in `movimenti`.

### `audio.py`
Gestisce la pipeline audio locale.
- `capture_audio()` legge il microfono e mette i chunk in `audio_queue`.
- `recognize_speech()` carica il modello Vosk e converte l’audio in testo, inserendo il risultato in `text_queue`.
- `run_tts()` sintetizza il testo tramite pyttsx3 e lo riproduce.
- `main()` dimostra il funzionamento stand-alone del modulo.
- `write_log()` traccia errori operativi e informazioni utili.

### `vision/vision.py`
Gestisce la videocamera e il riconoscimento facciale.
- La classe principale è `Vision`.
- Metodi principali:
  - `find_cameras()` — restituisce le webcam disponibili.
  - `start()` — avvia il thread di acquisizione video.
  - `_run_loop()` — legge i frame dalla camera, applica riconoscimento facciale e mostra il video.
  - `face_detection()` — usa `DeepFace.find()` e `DeepFace.analyze()` per identificare volti e analizzare emozioni.
- Registra nei log eventi come l’avvio della camera, errori di apertura e il riconoscimento delle persone.
- Memorizza l’ultima persona riconosciuta in `current_name` e uno storico leggero in `recognized_history`.

## Dettagli di ciascun modulo

### `main.py` — Sezioni principali

1. **Configurazione iniziale**
   - Importa e configura le variabili d’ambiente per ridurre i warning di TensorFlow/ABSL.
   - Attiva il logging centralizzato.

2. **Gestione movimenti seriali**
   - `execute_movement(par)` verifica che l’indice possa essere eseguito e invia il comando su seriale.
   - Registra successi e errori.

3. **Gestione comandi testuali**
   - `execute_command(command_text)` interpreta comandi come `/execute`, `/setIP`, `/setModel`, `/seeModel` e `/help`.
   - Per ogni comando valida gli argomenti e scrive i log.

4. **Prompt e risposta AI**
   - `create_prompt(message, people)` crea un prompt in formato JSON a partire da messaggio e persona riconosciuta.
   - `process_ai_prompt(raw_prompt, use_tts=False)` invia il prompt al client Ollama, gestisce il parsing della risposta e avvia l’esecuzione del movimento.

5. **Loop di esecuzione**
   - `handle_loop()` gestisce l’interazione testuale continua.
   - `handle_loop_audio()` è il ciclo alternativo per il riconoscimento vocale.

6. **Avvio dell’applicazione**
   - La sezione `if __name__ == "__main__"` avvia `Vision`, manda a chiamare Ollama e richiede all’utente porta seriale e camera.
   - Registra gli errori critici e gestisce `KeyboardInterrupt`.

### `utilities.py` — Sezioni principali

1. **Configurazione dei log**
   - `LOG_DIR` è la directory `logs/` nella radice del progetto.
   - `setup_logging(...)` crea il file `log-YYYY-MM-DD.log` e configura un logger con formattazione standard.
   - `logger.propagate = False` evita duplicazioni di messaggi.

2. **Scrittura log**
   - `write_log(message, level="info")` scrive i messaggi nel logger centralizzato.

3. **Funzioni di utilità**
   - `ping(host)` verifica la raggiungibilità del server con un ping di sistema e scrive i risultati nei log.

### `requests3.py` — Sezioni principali

1. **Configurazione Ollama**
   - Tenta di leggere la configurazione da `configuration.py` se presente.
   - In assenza di configurazione usa valori di default.

2. **Metodo `change_conf()`**
   - Aggiorna server IP, porta e modello.
   - Controlla la presenza dei modelli installati.

3. **Metodo `request()`**
   - Crea e invia la richiesta HTTP al servizio chat.
   - Registra payload, stato e risposta.
   - Restituisce il contenuto della risposta o la stringa raw in caso di parsing fallito.

4. **Funzioni modello**
   - `change_model(model)` controlla se il modello esiste e lo imposta.
   - `see_model()` recupera e aggiorna la lista dei modelli disponibili.

5. **Lista di movimenti**
   - `movimenti` è la lista delle stringhe riconosciute dal sistema AI per la gestione dei comandi.

### `audio.py` — Sezioni principali

1. **Pipeline audio**
   - `capture_audio()` legge il microfono e inserisce i chunk in `audio_queue`.
   - `recognize_speech()` converte l’audio in testo con Vosk.
   - `run_tts()` sintetizza testo con pyttsx3.

2. **Supporto logging**
   - Gli errori hardware audio e gli eventi TTS vengono registrati con `write_log()`.

3. **Esecuzione stand-alone**
   - `main()` permette di eseguire il modulo direttamente per testare la pipeline audio.

### `vision/vision.py` — Sezioni principali

1. **Inizializzazione**
   - `Vision.__init__()` crea le strutture per il thread, il blocco, la cache dei nomi riconosciuti e il percorso del database volti.

2. **Rilevazione camere**
   - `find_cameras()` restituisce la lista delle webcam disponibili.

3. **Avvio e interruzione**
   - `start()` configura la videocamera e avvia il thread di acquisizione.
   - `stop()` interrompe il thread e ripulisce le risorse.

4. **Ciclo di acquisizione**
   - `_run_loop()` legge i frame dalla camera, applica riconoscimento facciale e mostra una finestra di anteprima.

5. **Riconoscimento facciale**
   - `face_detection()` usa `DeepFace.find()` per identificare i volti e `DeepFace.analyze()` per stimare le emozioni.
   - Scrive su `recognition.txt` il nome dell’ultima persona riconosciuta.
   - Aggiorna `current_name` e la storia dei riconoscimenti.

## Note sulla struttura dei log

- I log vengono salvati in `logs/log-YYYY-MM-DD.log`.
- Tutti i moduli principali usano `utilities.write_log()` per mantenere una crittografia uniforme.
- Il logger registra messaggi `info`, `warning` ed `error` in modo coerente.

## Come orientarsi rapidamente

1. Per capire come funziona l’avvio dell’app prova subito `main.py`.
2. Per sapere come vengono formati e inviati i prompt leggi `requests3.py`.
3. Per analizzare la pipeline audio locale leggi `audio.py`.
4. Per la parte visione e riconoscimento facciale leggi `vision/vision.py`.
5. Per le funzioni comuni e la configurazione del logging leggi `utilities.py`.
