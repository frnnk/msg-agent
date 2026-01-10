"""
Entrypoint for FastAPI server.
"""

from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root():
    return "Hello world!"

@app.get('/health-check')
async def health():
    return "Server is healthy"

