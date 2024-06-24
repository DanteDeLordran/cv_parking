import asyncpg
from cryptography.fernet import Fernet
import os

DATABASE_URL = "postgresql://user:password@localhost:5432/estacionamiento"

# Configuración de cifrado
KEY = Fernet.generate_key()
cipher_suite = Fernet(KEY)

# Crear conexión a la base de datos
async def connect_db():
    return await asyncpg.connect(DATABASE_URL)

# Funciones para operaciones en la base de datos
async def create_user(username: str, password: str, profile: str):
    async with connect_db() as conn:
        encrypted_password = cipher_suite.encrypt(password.encode('utf-8')).decode('utf-8')
        await conn.execute("INSERT INTO users (username, password, profile) VALUES ($1, $2, $3)", username, encrypted_password, profile)

async def get_user(username: str):
    async with connect_db() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        if row:
            decrypted_password = cipher_suite.decrypt(row['password'].encode('utf-8')).decode('utf-8')
            return {"username": row['username'], "profile": row['profile'], "password": decrypted_password}
        else:
            return None

async def update_user_profile(username: str, new_profile: str):
    async with connect_db() as conn:
        await conn.execute("UPDATE users SET profile = $1 WHERE username = $2", new_profile, username)

async def delete_user(username: str):
    async with connect_db() as conn:
        await conn.execute("DELETE FROM users WHERE username = $1", username)

async def create_admin():
    # Crear usuario administrador por defecto
    await create_user("admin", "admin_password", "admin")

async def initialize_db():
    # Inicializar la base de datos (crear tablas, etc.)
    try:
        async with connect_db() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    profile TEXT NOT NULL
                )
            """)
        await create_admin()
    except Exception as e:
        print(f"Error initializing database: {e}")
