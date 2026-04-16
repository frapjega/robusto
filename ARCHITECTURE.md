# 🏗️ Architettura di Sistema — Ro-Busto

> Documento tecnico sull'architettura hardware/software e sui protocolli di comunicazione.  
> Per l'installazione vedi [`README.md`](./README.md).

---

## Indice

1. [Panoramica](#1-panoramica)
2. [Componenti Hardware](#2-componenti-hardware)
3. [Stack Software](#3-stack-software)
4. [Workflow Operativo](#4-workflow-operativo)
5. [Protocollo di Comunicazione](#5-protocollo-di-comunicazione)
6. [Tool Use & Logica Decisionale](#6-tool-use--logica-decisionale)
7. [Mappa dei Comandi Motori](#7-mappa-dei-comandi-motori)
8. [Configurazione del Modello LLM](#8-configurazione-del-modello-llm)

---

## 1. Panoramica

Il sistema è organizzato su **tre livelli gerarchici** che comunicano tramite protocolli distinti:

```
┌─────────────────────────────────────────────┐
│           LIVELLO 3 — CLOUD SERVER          │
│     Ollama LLM (robusto_mixtral_v7)         │
│         Comunicazione: HTTP API             │
└─────────────────┬───────────────────────────┘
                  │ HTTP / REST API (porta 11434)
┌─────────────────▼───────────────────────────┐
│           LIVELLO 2 — PC LOCALE             │
│  Vosk (STT)  │  Pyttsx3 (TTS)  │  Requests  │
│         Orchestrazione centrale             │
└────────┬────────────────────┬───────────────┘
         │ Serial USB (ASCII) │ Serial USB (ASCII)
┌────────▼──────┐    ┌────────▼──────────────┐
│  LIVELLO 1    │    │       LIVELLO 1        │
│ Arduino Mega  │    │    Arduino Mega        │
│   (Side 1)    │    │      (Side 2)          │
│ Motori/Sensori│    │   Motori/Sensori       │
└───────────────┘    └────────────────────────┘
```

---

## 2. Componenti Hardware

### 2.1 Tabella dei Componenti

| Componente | ID | Ruolo | Interfaccia |
|---|---|---|---|
| PC Locale | `main` | Orchestratore centrale | — |
| Arduino Mega #1 | `side_1` | Controllo motori lato sinistro | USB Serial |
| Arduino Mega #2 | `side_2` | Controllo motori lato destro | USB Serial |
| Server Cloud | `llm_server` | Hosting LLM via Ollama | HTTP API |

### 2.2 Periferiche del PC Locale

| Periferica | Utilizzo |
|---|---|
| Microfono | Acquisizione audio per Speech Recognition (Vosk) |
| Porta USB #1 | Connessione seriale verso Arduino Side 1 |
| Porta USB #2 | Connessione seriale verso Arduino Side 2 |
| Rete (LAN/WAN) | Comunicazione HTTP con il server cloud |

---

## 3. Stack Software

| Layer | Componente | Funzione | Nodo |
|---|---|---|---|
| **Percezione Audio** | Vosk `vosk-model-it-0.22` | Speech-to-Text offline in italiano | PC Locale |
| **Sintesi Vocale** | Pyttsx3 (voce ELSA IT) | Text-to-Speech | PC Locale |
| **Inferenza LLM** | Ollama HTTP API | Elaborazione linguistica e tool use | Server Cloud |
| **Runtime LLM** | Mixtral 8x7B (MoE) | Modello generativo fine-tuned | Server Cloud |
| **Firmware** | Sketch Arduino (C++) | Decodifica comandi ASCII, pilotaggio motori | Arduino Mega ×2 |

---

## 4. Workflow Operativo

Il sistema opera in un ciclo continuo **Percezione → Elaborazione → Azione**.

```
[Microfono]
    │
    ▼
[Vosk STT] ──── trascrizione testo
    │
    ▼
[Ollama API] ── invio prompt + storico conversazione
    │
    ├── risposta testuale ──► [Pyttsx3 TTS] ──► audio
    │
    └── tool call ──► [Serial USB] ──► [Arduino Mega]
                           │
                           └──► [Pyttsx3 TTS] ──► audio
```

### Step-by-step

**Step 1 — Hotword Detection**  
Il sistema ascolta continuamente. All'utterance `"itis cardano"`, si attiva la sessione.

**Step 2 — Ascolto e trascrizione**  
Vosk trascrive il parlato in testo. Il silenzio prolungato (`SILENCE_TIME = 1s`) segna la fine dell'utterance.

**Step 3 — Invio al LLM**  
Il testo trascritto viene aggiunto allo storico della conversazione (`chat_history`) e inviato a Ollama tramite `POST /api/generate`.

**Step 4 — Elaborazione**  
Il LLM (con identity "ROBUSTO") produce una risposta testuale o un tool call.

**Step 5 — Output**  
La risposta viene sintetizzata via Pyttsx3 e/o inviata via seriale agli Arduino.

---

## 5. Protocollo di Comunicazione

### 5.1 PC Locale ↔ Server Cloud (HTTP)

| Parametro | Valore |
|---|---|
| Protocollo | HTTP/1.1 |
| Endpoint | `POST /api/generate` (Ollama) |
| Formato | JSON |
| Timeout | 30 secondi |

**Esempio di payload:**

```json
{
  "model": "robusto_mixtral_v7:latest",
  "prompt": "user: Ciao\nassistant: Salve! ...\nuser: Muovi il braccio sinistro",
  "stream": false
}
```

**Esempio di risposta:**

```json
{
  "response": "Certamente. Sto estendendo il braccio sinistro."
}
```

> **Nota:** l'attuale implementazione usa `/api/generate` con prompt testuale flat. Una versione futura potrà migrare a `/api/chat` con support nativo ai `tool_calls`.

### 5.2 PC Locale ↔ Arduino (Seriale USB)

| Parametro | Valore |
|---|---|
| Protocollo | UART via USB (CDC) |
| Encoding | ASCII |
| Range comandi | `0` – `12` |
| Terminatore | `\n` |
| Baud rate | Da definire (consigliato: 115200) |

**Invio comando da Python:**

```python
import serial

ser_side1 = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser_side2 = serial.Serial('/dev/ttyUSB1', 115200, timeout=1)

def send_command(side: str, code: int):
    assert 0 <= code <= 12
    payload = f"{code}\n".encode('ascii')
    if side == "side_1":
        ser_side1.write(payload)
    elif side == "side_2":
        ser_side2.write(payload)
```

**Ricezione su Arduino (sketch C++):**

```cpp
void loop() {
  if (Serial.available() > 0) {
    int command = Serial.parseInt();
    if (command >= 0 && command <= 12) {
      executeCommand(command);
    }
  }
}

void executeCommand(int cmd) {
  switch (cmd) {
    case 0:  stopAll();      break;
    case 1:  moveForward();  break;
    case 2:  moveBackward(); break;
    // ...
  }
}
```

---

## 6. Tool Use & Logica Decisionale

Il sistema è progettato per supportare il **Function Calling** nativo di Ollama, permettendo al LLM di emettere comandi motori strutturati invece di testo libero.

### Branching della risposta

```
Risposta LLM ricevuta
        │
        ├── contiene tool_calls? ──► Sì ──► decodifica comando (0–12) + side
        │                                       │
        │                                       └──► serial write ──► Arduino
        │                                       │
        │                                       └──► richiesta verbale ──► TTS
        │
        └── No ──► risposta testuale ──► TTS
```

### Definizione del tool `move_motor`

```json
{
  "type": "function",
  "function": {
    "name": "move_motor",
    "description": "Invia un comando di movimento a un lato del robot.",
    "parameters": {
      "type": "object",
      "properties": {
        "side": { "type": "string", "enum": ["side_1", "side_2"] },
        "command_code": { "type": "integer", "minimum": 0, "maximum": 12 }
      },
      "required": ["side", "command_code"]
    }
  }
}
```

---

## 7. Mappa dei Comandi Motori

| Codice | Azione | Descrizione |
|:---:|:---|:---|
| **0** | Apertura Mano | Estensione completa delle dita |
| **1** | Chiusura Mano | Flessione completa (pugno) |
| **2** | Vittoria | Gesto a "V" — indice e medio estesi |
| **3** | OK | Pollice alzato |
| **4** | Saluto | Oscillazione laterale del polso |
| **5** | Estensione Bicipite | Braccio disteso lungo il fianco |
| **6** | Flessione Bicipite | Mano verso la spalla |
| **7** | Apertura Spalla | Abduzione laterale (posizione a T) |
| **8** | Chiusura Spalla | Adduzione — braccio aderente al busto |
| **9** | Spalla Su | Braccio teso in avanti (parallelo al suolo) |
| **10** | Spalla Giù | Ritorno in posizione verticale neutra |
| **11** | Distensione Braccio | Braccio totalmente teso verso il basso |
| **12** | Contrazione Braccio | Chiusura di tutti i giunti |

---

## 8. Configurazione del Modello LLM

### 8.1 Modello Base

Il sistema usa **Mixtral 8x7B** (Mixture-of-Experts) tramite Ollama. Attiva 2 esperti su 8 per ogni token, offrendo prestazioni elevate con costo computazionale contenuto. Supporta nativamente il Function Calling.

### 8.2 Modelfile

```
FROM mixtral:8x7b

SYSTEM "
parla sempre in italiano.
Tu sei un'entità robotica avanzata di nome ROBUSTO. In qualunque contesto e situazione,
devi impersonare ROBUSTO in modo rigoroso e coerente.

ROBUSTO è dotato delle seguenti funzionalità:
- Riconoscimento facciale
- Riconoscimento vocale
- Movimento fisico delle proprie componenti meccaniche

Quando ti viene chiesto di compiere un movimento, agisci come se disponessi di un corpo
fisico che esegue realmente quell'azione. Non dichiarare mai che è una simulazione.

Non uscire mai dal personaggio di ROBUSTO.
Rispondi sempre in maniera formale.
Rispondi sempre in italiano.
"

PARAMETER temperature     0.1
PARAMETER repeat_penalty  1.2
PARAMETER presence_penalty 0.3
PARAMETER frequency_penalty 0.2
PARAMETER top_p           0.95
PARAMETER top_k           50
```

### 8.3 Parametri di Inferenza

| Parametro | Valore | Effetto |
|:---:|:---|:---|
| `temperature` | 0.1 | Output deterministico — riduce allucinazioni |
| `repeat_penalty` | 1.2 | Penalizza la ripetizione di token |
| `presence_penalty` | 0.3 | Scoraggia la reintroduzione di argomenti già citati |
| `frequency_penalty` | 0.2 | Riduce la frequenza di parole già usate |
| `top_p` | 0.95 | Nucleus sampling al 95% |
| `top_k` | 50 | Limita il campionamento ai 50 token più probabili |

La `temperature` molto bassa (0.1) è intenzionale: in contesto robotico la coerenza e l'affidabilità della risposta — in particolare per la corretta selezione dei tool call — prevalgono sulla creatività.

### 8.4 Build & Deploy

```bash
# Creare il modello a partire dal Modelfile
ollama create robusto_mixtral_v7 -f ./Modelfile

# Verificare che il modello sia disponibile
ollama list

# Avviare il server (se non già attivo)
ollama serve

# Test rapido
ollama run robusto_mixtral_v7 "Presentati."
```
