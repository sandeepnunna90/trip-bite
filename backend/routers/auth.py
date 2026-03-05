from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.models import AuthResponse, SignupRequest, LoginRequest
from backend.services.supabase_client import get_anon_client
from backend.services.email_service import send_welcome_email
from backend.config import get_settings

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    client = get_anon_client()
    try:
        result = client.auth.get_user(token)
        if not result or not result.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"user_id": result.user.id, "token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/signup")
def signup(req: SignupRequest):
    client = get_anon_client()
    try:
        result = client.auth.sign_up({"email": req.email, "password": req.password})
        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed — check your email for confirmation.")
        send_welcome_email(req.email, req.name)
        return {"message": "Account created! Check your email to confirm your address."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    client = get_anon_client()
    try:
        result = client.auth.sign_in_with_password({"email": req.email, "password": req.password})
        if result.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return AuthResponse(
            access_token=result.session.access_token,
            user_id=str(result.user.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/google")
def google_oauth():
    settings = get_settings()
    client = get_anon_client()
    result = client.auth.sign_in_with_oauth({"provider": "google"})
    return {"url": result.url}
