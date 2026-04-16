# 🚀 Sviluppi Futuri — Ro-Busto

> Roadmap e idee per le prossime versioni del progetto.  
> Per l'architettura attuale vedi [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Priorità Alta — Da implementare a breve

### ✅ Feedback di esecuzione Arduino
Attualmente il sistema invia comandi agli Arduino senza verificare se l'azione sia stata eseguita correttamente. È necessario implementare un meccanismo di **acknowledgment** bidirezionale:
- L'Arduino restituisce al PC un codice di stato (`OK`, `ERR`, `TIMEOUT`) dopo ogni comando ricevuto.
- Il PC attende la conferma prima di procedere con la risposta vocale.
- In caso di errore, il sistema può ritentare o informare l'utente.

### ✅ Gestione errori sulla comunicazione seriale
La comunicazione USB/seriale è vulnerabile in ambienti rumorosi (disconnessioni, overflow del buffer, comandi corrotti). Sviluppare un layer robusto con:
- Timeout configurabile per la risposta dell'Arduino.
- Retry automatico in caso di mancata risposta.
- Log degli errori seriali su file.

### ✅ Logging e debug
Definire dove e come vengono salvati log ed informazioni di debug:
- File di log rotante (`robusto.log`) con timestamp, prompt inviati, risposte ricevute e comandi seriali.
- Livelli di log configurabili (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Possibilità di abilitare/disabilitare il logging da riga di comando.

---

## Priorità Media — Prossime iterazioni

### 🔧 Migrazione a `/api/chat` con tool use nativo
L'implementazione attuale usa `/api/generate` con un prompt testuale flat. Migrare all'endpoint `/api/chat` di Ollama per:
- Gestione nativa dello storico conversazione in formato JSON strutturato.
- Supporto ai `tool_calls` nella risposta, con parsing automatico del comando motore.
- Eliminazione della gestione manuale del `chat_history` concatenato come stringa.

### 🔧 Specifica dei collegamenti Arduino
Documentare in dettaglio:
- Quale pin di ogni Arduino Mega pilota quale attuatore (servo, motore DC, ecc.).
- Schema di collegamento elettrico tra Arduino e motori/sensori.
- Specifiche degli attuatori usati (tensione, corrente, range di movimento).

### 🔧 Specifica dell'hardware del server
Il server che esegue Ollama non è ancora documentato. Aggiungere:
- CPU, RAM, GPU (modello e VRAM).
- Sistema operativo e versione di CUDA/ROCm (se applicabile).
- Benchmark di latenza end-to-end misurata sull'hardware reale.

### 🔧 Monitoraggio della latenza
Il ciclo percezione → elaborazione → azione introduce una latenza che può rendere l'interazione innaturale. Misurare e ottimizzare:
- Latenza STT (Vosk): tempo dalla fine dell'utterance alla trascrizione.
- Latenza LLM (Ollama): tempo dalla request alla response.
- Latenza seriale: tempo dalla scrittura del comando all'esecuzione fisica.
- Definire una soglia massima accettabile (es. < 2 secondi end-to-end).

---

## Priorità Bassa — Idee future

### 💡 Modulo di Visione
Integrare una webcam e un modulo di computer vision per arricchire il contesto inviato al LLM:
- Riconoscimento facciale delle persone presenti nella scena.
- Il LLM potrà ricevere input del tipo: `"Persone rilevate: [Alice, Bob]. Bob sembra arrabbiato."`
- Tool dedicato: il modello potrà richiedere attivamente info visive (`"quante persone ci sono?"`, `"c'è Alice?"`).
- Candidati: OpenCV + DeepFace, o MediaPipe.

### 💡 Migrazione a Whisper per STT
Vosk offre buone prestazioni offline ma Whisper (OpenAI) garantisce accuratezza superiore, specialmente su parlato spontaneo e accenti regionali italiani. Valutare la migrazione mantenendo il supporto offline tramite `faster-whisper`.

### 💡 Supporto multi-piattaforma
L'attuale implementazione è ottimizzata per Windows (voce TTS ELSA, percorsi COM per Arduino). Aggiungere compatibilità con:
- **Linux/macOS**: sostituzione della voce TTS (es. `espeak-ng`, `festival`) e adattamento delle porte seriali (`/dev/ttyUSB*`).
- File di configurazione per la selezione automatica della piattaforma.

### 💡 Interfaccia web di amministrazione
Una semplice dashboard (es. Flask + HTML) per:
- Visualizzare lo storico della conversazione in tempo reale.
- Inviare comandi manuali agli Arduino senza passare dal LLM.
- Monitorare lo stato della connessione al server e agli Arduino.
- Cambiare l'IP del server senza riavviare il client.

### 💡 Modalità demo autonoma
Definire una sequenza di movimenti e frasi pre-programmate che ROBUSTO esegue in autonomia quando non riceve input per un certo periodo (es. saluto periodico, piccola coreografia), utile per esposizioni e fiere scolastiche.

---

## Issues note

| ID | Descrizione | Priorità |
|---|---|---|
| #1 | Nessun feedback dall'Arduino dopo l'esecuzione del comando | Alta |
| #2 | `chat_history` cresce indefinitamente (nessun limite di contesto) | Media |
| #3 | Eccezione generica nel `except` del flow testo — nasconde errori reali | Media |
| #4 | La voce TTS italiana (`ELSA`) è disponibile solo su Windows 10/11 | Bassa |
| #5 | `SILENCE_TIME = 1s` può tagliare frasi con pause naturali | Bassa |
