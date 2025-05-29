from fastapi import FastAPI
from .database import Base, engine
from .routers import users, projects, tasks, timesheet, approvals

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Time Tracker API")

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(timesheet.router)
app.include_router(approvals.router)

@app.get("/")
def root():
    return {"status": "Backend running"}
