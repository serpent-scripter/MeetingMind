from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import jwt
from fastapi.security import OAuth2PasswordBearer
from schemas.models import (
    UserCreate,
    UserLogin,
    UserResponse,
    SignupResponse,
    LoginResponse,
    LogoutResponse,
)
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
)
from db.database import get_db
from core.constants import ErrorMessages, SecurityConstants

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorMessages.CREDENTIALS_VALIDATION_FAILED,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[SecurityConstants.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    db = get_db()
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception

    return user


@router.post(
    "/signup", status_code=status.HTTP_201_CREATED, response_model=SignupResponse
)
async def signup(user: UserCreate):
    db = get_db()

    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=400, detail=ErrorMessages.EMAIL_ALREADY_REGISTERED
        )

    user_dict = {
        "email": user.email,
        "passwordHash": get_password_hash(user.password),
        "name": user.name,
        "storageUsed": 0,
        "createdAt": datetime.now(),
    }

    await db.users.insert_one(user_dict)

    return SignupResponse(
        email=user.email,
        name=user.name,
        storageUsed=0,
    )


@router.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    db = get_db()

    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INCORRECT_EMAIL_PASSWORD,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token}


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        email=str(current_user.get("email", "")),
        name=current_user["name"],
        storageUsed=current_user.get("storageUsed", 0),
    )
