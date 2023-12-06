from typing import Annotated
from fastapi import Depends, FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from .db import engine, create_db_and_tables
import logging

app = FastAPI(
    title="Tsunami Alert API",
    description="Know when an official Tsunami Threat has been issued for your location",
    version="0.0.1"
)

origins = [
    "http://localhost:8001",
    "https://localhost:8001",
    "http://fleet.airwarrior.net",
    "https://fleet.airwarrior.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def main():
    return {"detail": "Welcome to Tsunami Alert!"}
