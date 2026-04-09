from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.ai.face_auth import register_face, verify_face
from app.core.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class FaceRegisterRequest(BaseModel):
    images: List[str] # List of base64 encoded images
    operator_id: str

class FaceLoginRequest(BaseModel):
    image: str # Base64 encoded image
    operator_id: str

class IdValidateRequest(BaseModel):
    operator_id: str

# In a real system, these would be in a DB. Now using JSON persistence via store.py.
from app.database.store import is_operator_valid, add_operator

@router.post("/validate_id")
def validate_operator_id(data: IdValidateRequest):
    if not is_operator_valid(data.operator_id):
        raise HTTPException(status_code=403, detail="Operator ID revoked or unrecognized.")
    return {"message": "ID verified. Proceed to biometric scan.", "valid": True}

@router.post("/register_face")
def register_face_endpoint(data: FaceRegisterRequest):
    if not data.images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    success = register_face(data.images)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register face. Could not detect a face in the provided images.")
    
    # Store registration info dynamically
    # Normally we'd store a distinct hash. For demo we just register the access
    add_operator(data.operator_id, "active-biometric-hash-xyz123")
        
    return {"message": "Face registered successfully"}

@router.post("/login_face")
def login_face_endpoint(data: FaceLoginRequest):
    if not data.image:
        raise HTTPException(status_code=400, detail="No image provided")
        
    is_match, confidence = verify_face(data.image)
    if not is_match:
        if confidence == 999.9:
            raise HTTPException(status_code=401, detail="VISUAL THREAT DETECTED: Anti-Spoofing signature failed. Live organic feed required.")
        raise HTTPException(status_code=401, detail=f"Face matching failed or no face registered. (Score: {confidence})")
        
    # Face matched, create JWT token
    token = create_access_token(data={"sub": "1"}) # User ID 1
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Login successful"
    }

@router.get("/status")
def auth_status():
    from app.ai.face_auth import FACE_MODEL_PATH
    is_registered = FACE_MODEL_PATH.exists()
    return {"is_registered": is_registered}
