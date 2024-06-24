from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from db import get_user, update_user_profile, delete_user, initialize_db

security = HTTPBasic()

# Validación de credenciales
async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = await get_user(credentials.username)
    if not user or user['password'] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

# Verificar si es administrador
async def is_admin(user: dict = Depends(get_current_user)):
    if user['profile'] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

# Routers para administración de usuarios
async def create_new_user(username: str, password: str, profile: str):
    await create_user(username, password, profile)

async def modify_user_profile(username: str, new_profile: str):
    await update_user_profile(username, new_profile)

async def remove_user(username: str):
    await delete_user(username)

# Eventos de inicio y cierre de la aplicación
async def startup():
    await initialize_db()

async def shutdown():
    pass  # Opciones de respaldo de datos aquí
