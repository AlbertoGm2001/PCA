from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import home, events, classes, announcements, users, auth
from db.session import init_db

app = FastAPI(
    title="Padel Club API",
    description="Backend for Padel Club Management App",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include Routers
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(events.router)
app.include_router(classes.router)
app.include_router(announcements.router)
app.include_router(users.router)

@app.on_event("startup")
def on_startup():
    init_db()
    # pass

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Padel Club API",
        "docs": "/docs"
    }
