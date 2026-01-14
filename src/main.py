"""
Entrypoint for FastAPI server.
"""

from fastapi import FastAPI
import logging

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.INFO)

@app.get('/')
async def root():
    return "Hello world!"

@app.get('/health-check')
async def health():
    return "Server is healthy"

