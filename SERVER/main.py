import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user, otp, plate, decision, stats, error_notification
from logs import save_logs
from auth import startup, shutdown

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(user.router)
app.include_router(otp.router)
app.include_router(plate.router)
app.include_router(decision.router)
app.include_router(stats.router)
app.include_router(error_notification.router)

# Eventos de inicio y cierre de la aplicación
@app.on_event("startup")
async def on_startup():
    await startup()
    save_logs()

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
