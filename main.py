from dotenv import load_dotenv
from fastapi import FastAPI

from app.presentation.api import router

"""
Main entry point for the application.

This file is responsible for just initializing it and including the routes.
All the application logic is housed in app/*
"""

load_dotenv()
app = FastAPI()
app.include_router(router)
