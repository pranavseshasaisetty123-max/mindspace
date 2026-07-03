import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_utils import hash_password, verify_password, create_access_token, verify_access_token
from app.utils.security import rate_limit_auth

logger = logging.getLogger("mindspace.auth")
router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to retrieve the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token)
    if payload is None:
        logger.warning("Authentication failed: Invalid or expired JWT token.")
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Authentication failed: Token payload missing 'sub' claim.")
        raise credentials_exception
    
    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalars().first()
    if user is None:
        logger.warning(f"Authentication failed: User ID {user_id} not found in database.")
        raise credentials_exception
    return user

@router.post(
    "/api/v1/auth/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered and profile returned."},
        400: {"description": "Registration failed due to email already registered."},
        422: {"description": "Validation error (invalid email format or weak password)."}
    }
)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db), _rate_limit = Depends(rate_limit_auth)):
    """Register a new user account, hash their password, and save to the database."""
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        logger.warning(f"Registration failed: Email {user_data.email} is already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_pwd = hash_password(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_pwd)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"Successful registration for user email: {new_user.email} (ID: {new_user.id})")
    return new_user

@router.post(
    "/api/v1/auth/login", 
    response_model=TokenResponse,
    responses={
        200: {"description": "Credentials verified and access token returned."},
        401: {"description": "Incorrect email or password."},
        422: {"description": "Validation error (invalid data types)."}
    }
)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db), _rate_limit = Depends(rate_limit_auth)):
    """Authenticate user credentials (email/password) and issue a signed access token."""
    result = await db.execute(select(User).filter(User.email == credentials.email))
    user = result.scalars().first()
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Authentication failure: Incorrect credentials for login attempt: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    logger.info(f"Successful login for user email: {user.email} (ID: {user.id})")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get(
    "/api/v1/profile", 
    response_model=UserResponse,
    responses={
        200: {"description": "Profile loaded successfully."},
        401: {"description": "Could not validate credentials (missing or bad token)."}
    }
)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user profile."""
    return current_user
