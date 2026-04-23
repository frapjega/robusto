# 🤖 Ro-Busto

> **Versione:** 1.0.0 | **Stato:** In sviluppo  
> **Autori**(di v1.0.0)**:** Guido Gusberti, Alex Vadeu, Pietro Fratesi  
> **Istituto:** ITIS G. Cardano, Pavia  
> **Supervisore:** Prof. Ing. Nicola Muto  

---

## Cos'è Ro-Busto?

**Ro-Busto** è un robot umanoide open-source sviluppato come progetto extrascolastico presso l'ITIS G. Cardano di Pavia. Il sistema integra un modello LLM locale (Mixtral 8x7B via Ollama), riconoscimento vocale (Vosk), sintesi vocale (Pyttsx3) e controllo fisico dei motori tramite due Arduino Mega, il tutto orchestrato da un PC locale.

Il robot è in grado di:
- **Ascoltare** comandi vocali in italiano tramite hotword detection (`"itis cardano"`)
- **Ragionare** grazie a un LLM personalizzato con identità propria ("ROBUSTO")
- **Rispondere** a voce in italiano
- **Muoversi** fisicamente tramite 13 comandi motori distribuiti su due Arduino Mega

Per una descrizione dettagliata dell'architettura e dei protocolli di comunicazione, vedi [`ARCHITECTURE.md`](./ARCHITECTURE.md).  
Per gli sviluppi futuri pianificati, vedi [`FUTURE_DEVELOPMENTS.md`](./FUTURE_DEVELOPMENTS.md).

---

## Indice

- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Avvio](#avvio)
- [Comandi disponibili](#comandi-disponibili)
- [Modalità operative](#modalità-operative)
- [Struttura del progetto](#struttura-del-progetto)

---

## Requisiti

### Hardware
| Componente | Dettagli |
|---|---|
| PC Locale (Windows 10/11) | Orchestratore centrale |
| Arduino Mega x2 | Controllo motori lato sinistro e destro |
| Microfono USB | Acquisizione audio |
| Server con GPU | Hosting del modello LLM via Ollama |

### Software
- Python **3.9+**
- [Ollama](https://ollama.com/) installato sul server con il modello `robusto_mixtral_v7:latest`
- Modello Vosk per l'italiano: [`vosk-model-it-0.22`](https://alphacephei.com/vosk/models)
- Voce TTS italiana installata su Windows: `TTS_MS_IT-IT_ELSA_11.0`

### Dipendenze Python

```bash
pip install requests pyttsx3 pyaudio vosk
```

> **Nota:** su alcune macchine PyAudio richiede i binari di PortAudio. Su Windows si consiglia di installarlo tramite un wheel precompilato:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/itis-cardano/ro-busto.git
cd ro-busto
```

### 2. Installa le dipendenze Python

```bash
pip install -r requirements.txt
```

### 3. Scarica il modello Vosk

Scarica [`vosk-model-it-0.22`](https://alphacephei.com/vosk/models) e decomprimi la cartella nella root del progetto:

```
ro-busto/
├── vosk-model-it-0.22/   ← qui
├── finalfile.py
└── ...
```

### 4. Configura e avvia il server Ollama

Sul server cloud (o in locale), assicurati che Ollama sia in esecuzione con il modello personalizzato:

```bash
# Crea il modello a partire dal Modelfile
ollama create robusto_mixtral_v7 -f ./Modelfile

# Verifica che il modello sia presente
ollama list

# Avvia il server (porta default: 11434)
ollama serve
```

---

## Configurazione

All'avvio, il client legge l'IP del server da `config.txt` nella root del progetto. Se il file non esiste, viene usato l'IP di default `10.110.99.5`.

Per cambiare l'IP senza modificare il file manualmente, usa il comando `/cambia_ip` a runtime (vedi [Comandi disponibili](#comandi-disponibili)).

### Modifica manuale

Crea (o modifica) `config.txt` nella root:

```
192.168.1.100
```

### Parametri principali in `finalfile.py`

| Variabile | Valore default | Descrizione |
|---|---|---|
| `PORT` | `11434` | Porta del server Ollama |
| `MODEL_NAME` | `robusto_mixtral_v7:latest` | Nome del modello Ollama da usare |
| `MODEL_PATH` | `vosk-model-it-0.22` | Percorso del modello Vosk |
| `RATE` | `16000` | Sample rate audio (Hz) |
| `SILENCE_TIME` | `1` | Secondi di silenzio per terminare l'ascolto |

---

## Avvio

```bash
python finalfile.py
```

All'avvio il programma:
1. Verifica la connessione al server Ollama
2. Mostra il banner ASCII "ITIS CARDANO"
3. Chiede se usare la modalità voce o testo

---

## Modalità operative

### Modalità Testo (default)
Interazione tramite terminale: inserisci il prompt e leggi la risposta del modello.

### Modalità Voce
Attivazione tramite hotword: pronuncia **"itis cardano"** per iniziare l'ascolto. Il robot risponde a voce tramite la sintesi TTS.

Per uscire dalla modalità voce, pronuncia **"esci"**.

---

## Comandi disponibili

Validi in modalità testo:

| Comando | Descrizione |
|---|---|
| `esci` / `/esci` / `exit` | Termina la sessione |
| `/info` | Mostra le specifiche tecniche del modello Mixtral 8x7B |
| `/ping` | Verifica la connessione al server |
| `/cambia_ip` | Aggiorna l'IP del server (viene salvato in `config.txt`) |

---

## Struttura del progetto

```
ro-busto/
├── finalfile.py              # Script principale
├── config.txt                # IP del server (auto-generato)
├── Modelfile                 # Configurazione del modello Ollama
├── vosk-model-it-0.22/       # Modello ASR italiano (da scaricare)
├── requirements.txt          # Dipendenze Python
├── README.md                 # Questo file
├── ARCHITECTURE.md           # Architettura e protocolli
└── FUTURE_DEVELOPMENTS.md    # Roadmap e sviluppi futuri
```

---

## Licenza

Progetto sviluppato a scopo educativo nell'ambito delle attività extrascolastiche dell'ITIS G. Cardano di Pavia.
