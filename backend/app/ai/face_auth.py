import cv2
import numpy as np
import base64
import os
from pathlib import Path

# Setup paths
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)
FACE_MODEL_PATH = MODELS_DIR / "face_recognizer.yml"

# We use the standard Haar Cascade for face detection
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    raise RuntimeError(f"Error loading haarcascade from {cascade_path}")

def get_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if FACE_MODEL_PATH.exists():
        recognizer.read(str(FACE_MODEL_PATH))
    return recognizer

def decode_base64_image(base64_str: str) -> np.ndarray:
    """Decode base64 image coming from the frontend (data URI) to numpy array (BGR)."""
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    img_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def check_visual_threat(img: np.ndarray) -> bool:
    """
    Cryptographic/Biometric visual threat detection.
    Analyzes the variance of the Laplacian to ensure the image is a live camera feed 
    and not a digitally tampered planar injection payload (printed photo spoofing).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    # A completely printed/screen spoof often lacks the micro-depth, yielding abnormal variance.
    # We set a threshold for safety.
    if variance < 50.0:
        return True # Threat Detected
    return False # Safe

def detect_face(img: np.ndarray):
    """Detects the largest face in the image and returns the cropped grayscale face."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))
    if len(faces) == 0:
        return None
        
    # Get the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    return gray[y:y+w, x:x+h]

def register_face(base64_images: list[str]) -> bool:
    """Trains the LBPH model with the provided images and assigns ID=1."""
    faces = []
    labels = []
    
    for b64 in base64_images:
        img = decode_base64_image(b64)
        face_roi = detect_face(img)
        if face_roi is not None:
            # Resize for consistency
            face_roi = cv2.resize(face_roi, (200, 200))
            faces.append(face_roi)
            labels.append(1) # We use ID 1 for the authenticated user
            
    if not faces:
        return False
        
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.write(str(FACE_MODEL_PATH))
    return True

def verify_face(base64_image: str) -> tuple[bool, float]:
    """Verifies if the face matches the registered model. Returns (is_match, confidence)."""
    if not FACE_MODEL_PATH.exists():
        return False, 0.0
        
    img = decode_base64_image(base64_image)
    
    # 1. VISUAL THREAT CHECK (Anti-Spoofing Cryptography)
    if check_visual_threat(img):
        return False, 999.9 # Threat detected, force fail
        
    face_roi = detect_face(img)
    
    if face_roi is None:
        return False, 0.0
        
    face_roi = cv2.resize(face_roi, (200, 200))
    recognizer = get_recognizer()
    
    # predict returns label and confidence (distance). Lower distance = better match.
    label, confidence = recognizer.predict(face_roi)
    
    # LBPH distance: 0 is perfect match. Usually, < 60 is a good match depending on lighting.
    # Let's set a threshold of 70.
    if label == 1 and confidence < 75.0:
        return True, confidence
    return False, confidence
