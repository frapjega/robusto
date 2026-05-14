# from ast import main
import requests
from pythonping import ping
import subprocess
import os
import datetime
from utilities import write_log


try:    
    from configuration import config
    conf = config()
except ImportError:
    print("Avviso: File di configurazione non trovato, usando configurazione predefinita")

class ollama:
    def __init__(self, IP_ollama="127.0.0.1", port="11434", model='llama3.2'):
        """Initialize the ollama class with the IP address, port and model to be used"""
        # self.IP_server = IP_ollama
        try:
            self.IP_server = conf.IP_server
            self.model = conf.model_Ollama
            self.port = conf.port_server
        except:
            self.IP_server = IP_ollama
            self.port = port
            self.model = model
        self.history = []
        write_log(f"inizialized ollama")

    def change_conf(self, IP_ollama=None, port=None, model=None):
        """Verifica se il server è raggiungibile e se il modello scelto è presente."""
        self.IP_server = IP_ollama or self.IP_server
        self.port = port or self.port
        self.model = model or self.model
        

        changes = []
        if IP_ollama: changes.append(f"IP: {IP_ollama}")
        if port:      changes.append(f"port: {port}")
        if model:     changes.append(f"model: {model}")
        
        msg = f"Changed Ollama config: {', '.join(changes)}" if changes else "Ollama config called with no changes."
        write_log(msg)

        try:
            # Chiamata per ottenere tutti i modelli installati localmente
            response = requests.get(f"http://{self.IP_server}:{self.port}/api/tags", timeout=5)
            response.raise_for_status()
            
            models_data = response.json()
            # Estraiamo i nomi dei modelli presenti
            self.models = [m['name'] for m in models_data.get('models', [])]
            
            # Controlliamo se il nostro modello (o la sua versione :latest) esiste nella lista
            model_exists = self.model in self.models or f"{self.model}:latest" in self.models
            
            return True, model_exists
            
        except requests.RequestException as e:
            self.models = []
            write_log(f"error: {e} changing ollama config")
            return False, e
        

    def check_IP(self, IP = None):
        """Check the internet connession, return True if it work correctly, else return the status code/error if it is different from 200 """
        if IP is not None:
            try:
                url = f"http://{IP}:{self.port}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    #print("✅ Connessione al server riuscita.\n")
                    write_log(f"check ollama server status, HTTP status code: {response.status_code}")
                    return True
                else:
                    #print(f"⚠️ Server risponde con codice: {response.status_code}")
                    write_log(f"check ollama server status, HTTP status code: {response.status_code}")
                    return response.status_code
            except requests.exceptions.RequestException as e:
                #print("❌ Impossibile connettersi al server:")
                #print(e)
                write_log(f"check ollama server status, error: {e}")
                return e
            
        else:
            
            try:
                url = f"http://{self.IP_server}:{self.port}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    #print("✅ Connessione al server riuscita.\n")
                    write_log(f"check ollama server status, HTTP status code: {response.status_code}")
                    return True
                else:
                    #print(f"⚠️ Server risponde con codice: {response.status_code}")
                    write_log(f"check ollama server status, HTTP status code: {response.status_code}")
                    return response.status_code
            except requests.exceptions.RequestException as e:
                #print("❌ Impossibile connettersi al server:")
                #print(e)
                write_log(f"check ollama server status, error: {e}")
                return e
        



    movimenti = ["apri mano", "chiudi mano", "gesto vittoria", "OK", "saluto", "estensione bicipite", "flessione bicipite", "apertura spalla", "chiusura spalla", "spalla su", "spalla giu", "distensione braccio", "contrazione braccio", "none"]

    def request(self, question: str, timeout=30, movimenti_disponibili = movimenti):
        self.history.append({"role": "user", "content": question})
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "response" : {"type": "string"},
                    "movement" : {
                        "type": "string",
                        "enum": movimenti_disponibili}
                }, 
                "required": ["response", "movement"]
            }
        }
        # print(payload)
        write_log(f"ollama request, payload: {payload}")
        response = requests.post(f"http://{self.IP_server}:{self.port}/api/chat", 
                            json=payload,
                            timeout=timeout)
        
        write_log(f"ollama request, status code: {response.status_code}")
        write_log(f"ollama request, response: {response.text}")

        # print(response.text)

        try:    
            response_data = response.json()
            self.history.append({"role": response_data['message']['role'], "content": response_data['message']['content']})
            return response_data['message']['content']
        except:
            return response_data


    def change_model(self, model):
        """permised to chage the corrent model. if the changing was sucsesfull ruturn True"""
        self.see_model() 
        if not model in self.models:
            #print("model non finded")
            write_log(f"impossible use {model} as model (non installed on the server)")
            return False
        else:
            self.model = model
            #print(f"model to be used changed, now is using {self.model}")
            write_log(f"changing self.model to {model}")
            return True

    def see_model(self):
        """return a dict with all model on the server"""
        try:
            response = requests.get(f"http://{self.IP_server}:{self.port}/api/tags")
            models_data = response.json()
            self.models = [model['name'] for model in models_data.get('models', [])]
            write_log(f"updating models list: {self.models}")
            return True, self.models

        except Exception as e:
            write_log(f"impossible update models list: {e}")
            return False, None
        

Ollama = ollama()
#print(conf.model_Ollama)

if __name__ == "__main__":
    ollama_instance = ollama()
    ollama_instance.change_conf()
    print(ollama_instance.see_model())
    print()
    print(ollama_instance.request(prompt="sai alzare la spalla?"))