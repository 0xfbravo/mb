import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app import DependencyInjection, RequestLoggerMiddleware, router, setup_loguru

"""
Main entry point for the application.

This file is responsible for just initializing it and including the routes.
All the application logic is housed in app/*
"""

setup_loguru()
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_pool_min_size = os.getenv("DB_POOL_MIN_SIZE")
    db_pool_max_size = os.getenv("DB_POOL_MAX_SIZE")
    db_pool_max_idle = os.getenv("DB_POOL_MAX_IDLE")
    db_pool_timeout = os.getenv("DB_POOL_TIMEOUT")

    if not db_name or not db_user or not db_password or not db_host or not db_port:
        raise ValueError("Missing required environment variables")

    di = DependencyInjection()

    try:
        pool_min_size = int(db_pool_min_size) if db_pool_min_size else 1
        pool_max_size = int(db_pool_max_size) if db_pool_max_size else 10
        pool_max_idle = int(db_pool_max_idle) if db_pool_max_idle else 300
        pool_timeout = int(db_pool_timeout) if db_pool_timeout else 30
        await di.initialize(
            db_name,
            db_user,
            db_password,
            db_host,
            int(db_port),
            pool_min_size,
            pool_max_size,
            pool_max_idle,
            pool_timeout,
        )
        di.logger.info("Dependency injection initialized successfully.")
    except Exception as e:
        di.logger.error(f"Error during startup: {e}")
        # Don't raise the exception immediately but mark it as unhealthy
        di.logger.warning("Application starting with database initialization failure")

    yield

    try:
        await di.shutdown()
        di.logger.info("Dependency injection shutdown complete.")
    except Exception as e:
        di.logger.error(f"Error during shutdown: {e}")
        # Don't re-raise shutdown errors as they're not critical


# Create app with lifespan handler
title = os.getenv("TITLE", "")
version = os.getenv("VERSION", "")
description = os.getenv("DESCRIPTION", "")
app = FastAPI(
    title=title,
    contact={
        "name": "Fellipe Bravo",
        "url": "https://github.com/0xfbravo",
        "email": "0xfbravo@gmail.com",
    },
    description=description,
    version=version,
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


app.include_router(router)
app.add_middleware(RequestLoggerMiddleware)
