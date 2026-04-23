import cv2 
from deepface import DeepFace 
import pathlib 
import platform 
from pathlib import Path 

class Vision: 
    def __init__(self,): 
        self._cap = cv2.VideoCapture(0) # Prende videocamera default 
        self._working_path = pathlib.Path().resolve() 
        self._saved_name = set()
        self.last_person_found = False
        self.last_name = None
        
        # Esegue il sistema visivo del pc e seleziona quale usare 
        # Nella versione threaded non puoi usare questo 
    def run(self, face_detect: bool = True, object_detect: bool = False): 
        
        print("DB path:", str((self._working_path.parent / "assets" / "faces").resolve())) 
        
        if platform.system() == "Windows": 
            db_path = ("assets\\faces") 
        else: db_path = ("assets/faces") 
        
        print("Premi 'q' per uscire") 
        
        while True: 
            
            _, img = self._cap.read() 
            
            if face_detect: 
                img = self.face_detection(img, db_path) 
            
            if object_detect: 
                pass 
            
            cv2.imshow("Recognition", img) 
            
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break   

    def face_detection(self, img, db_path): 
        
        results = DeepFace.find(img, db_path, enforce_detection=False, silent=True)

        THRESHOLD = 0.6 # distanza massima per riconoscere una persona
        
        # ------------------ SE NON CI SONO RISULTATI ------------------
        if not results or all(r.empty for r in results):
            if self.last_person_found:       # stampo 1 volta
                with open("riconoscimenti.txt", "w") as f:
                    f.write("") # file vuoto
                print("Nessuna persona presente")
            self.last_person_found = False
            self.last_name = None
            return img
        
        # DeepFace.find può restituire più dataframe → iteriamo
        for df in results:
            if df.empty:
                continue

            # Coordinate volto
            x = df['source_x'][0]
            y = df['source_y'][0]
            w = df['source_w'][0]
            h = df['source_h'][0]

            # Nome cartella
            identity_path = df['identity'][0]
            name = Path(identity_path).parent.name

            # Distanza → più bassa = più simile
            distance = df["distance"][0]

            # ------------------ CONTROLLO CONFIDENCE ------------------
            # Se distanza > 0.6 → NON riconosciuto
            if distance > THRESHOLD:
                if self.last_person_found:
                    with open("riconoscimenti.txt", "w") as f:
                        f.write("")
                    print("Nessuna persona presente")
                self.last_person_found = False
                self.last_name = None
                return img

            # ------------------ STAMPA SOLO UNA VOLTA ------------------
            if name != self.last_name:
                self.last_name = name
                self.last_person_found = True
                with open("riconoscimenti.txt", "w") as f:
                    f.write(name + "\n")

            # ------------------ EMOTION ANALYSIS ------------------
            face_roi = img[y:y + h, x:x + w]
            analysis = DeepFace.analyze(face_roi, ['emotion'], silent=True, enforce_detection=False)

            # ------------------ DISEGNO SULLO SCHERMO ------------------
            cv2.putText(img, f'{name}', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
            cv2.putText(img, f'Emozione: {analysis[0]["dominant_emotion"]}', (x, y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0))

        return img