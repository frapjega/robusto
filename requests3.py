from ast import main
import requests

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

    def load_conf(self, IP_ollama=None, port=None, model=None):
        """Load configuration in the ollama class, check the internet connection"""
        self.IP_server = IP_ollama or self.IP_server
        self.port = port or self.port
        self.model = model or self.model
        # self.history = []
        #print("Everything loaded correctly")
        try:
            response = requests.get(f"http://{self.IP_server}:{self.port}/api/tags")
            models_data = response.json()
            self.models = [model['name'] for model in models_data.get('models', [])]
            #print("models find correcty\nconection with the server work correctly")
            return True
        except requests.RequestException as e:
            #print(f"Error connecting to the Ollama server: {e}")
            self.models = []
            return False

    def check_IP(self):
        """Check the internet connession, return True if it work correctly, else return the status code/error if it is different from 200 """
        try:
            url = f"http://{self.IP_server}:{self.port}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                #print("✅ Connessione al server riuscita.\n")
                return True
            else:
                #print(f"⚠️ Server risponde con codice: {response.status_code}")
                return response.status_code
        except requests.exceptions.RequestException as e:
            #print("❌ Impossibile connettersi al server:")
            #print(e)
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
        response = requests.post(f"http://{self.IP_server}:{self.port}/api/chat", 
                            json=payload,
                            timeout=timeout)
        
        try:    
            response_data = response.json()
            self.history.append({"role": response_data['message']['role'], "content": response_data['message']['content']})
            return response_data['message']['content']
        except:
            return response_data


    def change_model(self, model):
        """permised to chage the corrent model. if the changing was sucsesfull ruturn True"""
        if not model in self.models:
            #print("model non finded")
            return False
        else:
            self.model = model
            #print(f"model to be used changed, now is using {self.model}")
            return True

    def see_model(self):
        """return a dict with all model on the server"""
        response = requests.get(f"http://{self.IP_server}:{self.port}/api/tags")
        models_data = response.json()
        self.models = [model['name'] for model in models_data.get('models', [])]
        return self.models

#print(conf.model_Ollama)

if __name__ == "__main__":
    ollama_instance = ollama()
    ollama_instance.load_conf()
    print(ollama_instance.see_model())
    print()
    print(ollama_instance.request(prompt="sai alzare la spalla?"))