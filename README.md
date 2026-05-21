# RO-BUSTO 

> **Versione:** 1.0.0  
> **Autori:** Pietro Fratesi (frapjega)  
> **Istituto:** ITIS G. Cardano, Pavia (PV)  
> **Svulippato nell'ambito di:** Ro-Busto scuola futura

**RO-BUSTO** è un sistema robotico interattivo dotato di riconoscimento facciale, riconoscimento vocale e controllo fisico di componenti meccaniche tramite porta seriale. Il comportamento dell'IA è gestito da un modello LLM locale tramite [Ollama](https://ollama.com).

---

## Funzionalità

- **Riconoscimento facciale** — identifica persone tramite webcam usando DeepFace; analizza anche le emozioni in tempo reale.
- **Interazione AI** — risponde in linguaggio naturale tramite un modello LLM locale (default: `mistral-small3.2`) con il personaggio ROBUSTO.
- **Controllo movimenti** — invia comandi seriali per eseguire movimenti fisici (braccia, mani, collo).
- **Riconoscimento vocale** *(opzionale)* — converte l'audio del microfono in testo tramite Vosk e risponde con sintesi vocale via pyttsx3.
- **Logging** — tutti gli eventi vengono registrati in `logs/log-YYYY-MM-DD.log`.

---

## Requisiti di sistema

| Componente | Versione minima |
|---|---|
| Python | 3.9+ |
| Ollama | qualsiasi versione recente |
| Webcam | qualsiasi webcam compatibile con OpenCV |
| Porta seriale | opzionale (per i movimenti fisici) |

---

## Installazione

### 1. Clona il repository

**Linux / macOS**
```bash
git clone https://github.com/frapjega/robusto.git
cd robusto
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/frapjega/robusto.git
cd robusto
```

---

### 2. Crea l'ambiente virtuale Python

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Se PowerShell blocca l'esecuzione degli script, esegui prima:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### 3. Installa le dipendenze

**Linux / macOS**
```bash
pip install -r requirements.txt
```

**Windows**
```powershell
pip install -r requirements.txt
```

> ⚠️ **DeepFace** richiede TensorFlow. Su Windows assicurati di avere installato [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).

---

### 4. Scarica il modello Vosk *(per il riconoscimento vocale)*

Scarica il modello italiano da [alphacep.com/models](https://alphacep.com/models.html) e posiziona la cartella estratta nella root del progetto rinominandola `model/`:

```
robusto/
└── model/
    ├── am/
    ├── conf/
    └── ...
```

---

### 5. Configura Ollama e importa il modello

Assicurati che Ollama sia in esecuzione sul tuo sistema o su un server raggiungibile.

**Importa il modello ROBUSTO:**

**Linux / macOS**
```bash
ollama create robusto -f docs/Modelfile.txt
```

**Windows**
```powershell
ollama create robusto -f docs\Modelfile.txt
```

**Verifica che Ollama risponda:**
```bash
curl http://127.0.0.1:11434/api/tags
```

---

### 6. Aggiungi i volti da riconoscere

Crea la cartella `assets/faces/` e organizza le foto per persona:

```
assets/
└── faces/
    ├── Mario/
    │   ├── foto1.jpg
    │   └── foto2.jpg
    └── Giulia/
        └── foto1.jpg
```

Il nome della cartella viene usato come nome della persona riconosciuta.

---

## Avvio

```bash
python main.py

python main.py
```

All'avvio il sistema richiede interattivamente:
1. Il modello Ollama da usare
2. La porta seriale (invio per saltare)
3. L'indice della webcam da usare

---

## Comandi disponibili

Durante l'esecuzione puoi digitare messaggi liberi o usare i comandi seguenti:

| Comando | Descrizione |
|---|---|
| `/execute [0-12]` | Esegue un movimento specifico |
| `/setIP [IP]` | Cambia l'IP del server Ollama |
| `/setModel [nome]` | Imposta il modello LLM da usare |
| `/seeModel` | Elenca i modelli disponibili sul server |
| `/help` | Mostra l'elenco dei comandi |

---

## Struttura del progetto

```

robusto/
├── main.py                 # Entrypoint — ciclo principale, comandi e interazione utente
├── requirements.txt        # Dipendenze Python
├── recognition.txt         # File di output per il riconoscimento
├── README.md               # Documentazione principale del progetto
│
├── src/                    # Codice sorgente dell'applicazione
│   ├── api/
│   │   ├── requests3.py    # Client Ollama — invio prompt e gestione risposte AI
│   │   └── utilities.py    # Funzioni di utilità condivise
│   ├── audio/
│   │   ├── audio.py        # Pipeline audio: cattura, STT (Vosk) e TTS (pyttsx3)
│   │   └── vosk-model-small-it-0.22.zip # Modello di riconoscimento vocale Vosk
│   ├── log/
│   │   └── log.py          # Gestione e configurazione del sistema di logging
│   └── vision/
│       └── vision.py       # Riconoscimento facciale con DeepFace
│
├── assets/
│   └── faces/              # Database foto per il riconoscimento facciale
│       ├── Eddy/           # Immagini di target per il volto di Eddy
│       ├── Lucas/          # Immagini di target per il volto di Lucas
│       ├── Malek/          # Immagini di target per il volto di Malek
│       ├── Pietro/         # Immagini di target per il volto di Pietro
│       └── Prof Muto/      # Immagini di target per il volto del Prof Muto
│
├── docs/
│   ├── Modelfile.txt       # Definizione del personaggio ROBUSTO per Ollama
│   └── structure.md        # Note interne sulla struttura
│
└── logs/                   # Log giornalieri generati automaticamente (es. log-YYYY-MM-DD.log)

```

---

## Note

- Il file `recognition.txt` nella root viene aggiornato in tempo reale con il nome dell'ultima persona riconosciuta.
- Il parametro `THRESHOLD` in `vision.py` (default `0.5`) controlla la soglia di confidenza del riconoscimento facciale: abbassarlo rende il riconoscimento più severo.
- La cronologia della conversazione con Ollama viene mantenuta in memoria per tutta la sessione e azzerata al riavvio.
- Il modulo audio (`handle_loop_audio`) è presente ma disabilitato di default: per attivarlo decommentare le righe relative in `main.py`.
