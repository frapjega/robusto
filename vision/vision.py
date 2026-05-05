import cv2
from cv2_enumerate_cameras import enumerate_cameras
from deepface import DeepFace
import pathlib
import platform
from pathlib import Path
import threading
import collections
import time

class Vision:
    def __init__(self):
        self._cap = None
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._working_path = pathlib.Path(__file__).resolve()
        self._saved_name = set()
        self.last_person_found = False
        self.last_name = None
        self.current_name = None
        self.recognized_history = collections.deque(maxlen=50)
        self._show_window = True
        self.face_detect = True
        self.object_detect = False
        self._db_path = self._get_db_path()

    def _get_db_path(self):
        try:
            return str((self._working_path.parent / "assets" / "faces").resolve())
        except Exception as e3:
            print(f"Errore durante il recupero del percorso del database: {e3}")
            return None            
        

    def find_cameras(self):
        available_cameras = []
        for camera_info in enumerate_cameras():
            print(f"Fotocamera trovata: {camera_info.name} (Indice: {camera_info.index})")
            available_cameras.append({
                "index": camera_info.index,
                "name": camera_info.name,
                "backend": camera_info.backend
            })
        return available_cameras



    def start(self, face_detect: bool = True, object_detect: bool = False, show_window: bool = True, camera: int = 0):
        if self._thread and self._thread.is_alive():
            return

        self.face_detect = face_detect
        self.object_detect = object_detect
        self._show_window = show_window
        self._stop_event.clear()
        self._cap = cv2.VideoCapture(camera) #### 4
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def run(self, face_detect: bool = True, object_detect: bool = False, show_window: bool = True):
        self.start(face_detect=face_detect, object_detect=object_detect, show_window=show_window)
        if self._thread:
            self._thread.join()

    def stop(self):
        self._stop_event.set()
        if self._thread and threading.current_thread() is not self._thread:
            self._thread.join(timeout=2)
        self._cleanup()

    def _run_loop(self):
        print("DB path:", self._db_path)
        print("Premi 'q' per uscire")

        if not self._cap or not self._cap.isOpened():
            print("Errore: impossibile aprire la videocamera")
            return

        while not self._stop_event.is_set():
            ok, img = self._cap.read()
            if not ok or img is None:
                time.sleep(0.05)
                continue

            if self.face_detect:
                img = self.face_detection(img)

            if self.object_detect:
                pass

            if self._show_window:
                cv2.imshow("Recognition", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()
                    break

        self._cleanup()

    def _cleanup(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        if self._show_window:
            cv2.destroyAllWindows()

    def get_last_recognized(self):
        with self._lock:
            return self.current_name

    def get_recognized_history(self):
        with self._lock:
            return list(self.recognized_history)

    def clear_recognized_history(self):
        with self._lock:
            self.recognized_history.clear()
            self.current_name = None

    def face_detection(self, img):
        results = DeepFace.find(img, self._db_path, enforce_detection=False, silent=True)

        THRESHOLD = 0.5 # confidence threshold for face recognition

        if not results or all(r.empty for r in results):
            if self.last_person_found:
                with open("recognition.txt", "w") as f:
                    f.write("")
                print("Nessuna persona presente")
            self.last_person_found = False
            self.last_name = None
            with self._lock:
                self.current_name = None
            return img

        for df in results:
            if df.empty:
                continue

            x = int(df['source_x'][0])
            y = int(df['source_y'][0])
            w = int(df['source_w'][0])
            h = int(df['source_h'][0])

            identity_path = df['identity'][0]
            name = Path(identity_path).parent.name
            distance = float(df["distance"][0])

            if distance > THRESHOLD:
                if self.last_person_found:
                    with open("recognition.txt", "w") as f:
                        f.write("")
                    print("Nessuna persona presente")
                self.last_person_found = False
                self.last_name = None
                with self._lock:
                    self.current_name = None
                return img
            

            if name != self.last_name:
                self.last_name = name
                self.last_person_found = True
                with open("recognition.txt", "w") as f:
                    f.write(name + "\n")
                with self._lock:
                    self.current_name = name
                    self.recognized_history.append(name)

            face_roi = img[y:y + h, x:x + w]
            analysis = DeepFace.analyze(face_roi, ['emotion'], silent=True, enforce_detection=False)

            cv2.putText(img, f'{name}', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
            cv2.putText(img, f'Emozione: {analysis[0]["dominant_emotion"]}', (x, y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0))

        return img


if __name__ == "__main__":
    vision = Vision()
    print("input video disponibili:")
    cam_list = vision.find_cameras()

    for i in range(len(cam_list)):
        print(str(i) +": "+ cam_list[i]['name'])

    num_cam = int(input("a quale camera ti vuoi connettere?"))
    cam_index = cam_list[num_cam]['index']
    print(cam_index)
    print(cam_list)
    try:
        cam = int(cam_index)
    except:
        print("inserisci un indice tra quelli indicati")

    vision.start(camera=cam)

    try:
        while True:
            last = vision.get_last_recognized()
            if last is not None:
                print("Ultima persona riconosciuta:", last)
            time.sleep(1)
    except KeyboardInterrupt:
        vision.stop()
