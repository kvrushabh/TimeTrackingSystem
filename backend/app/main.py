from fastapi import FastAPI
from .database import Base, engine
from .routers import users, projects, tasks, auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Time Tracker API")

# CORS settings
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefix all routers with "/api"
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Backend running"}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/robots.txt',include_in_schema=False)
def robots():
    return FileResponse("robots.txt")
