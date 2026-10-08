#!/usr/bin/env python3
"""
Servidor Web para UDYAT APPS (AltStore / SideStore source).
Sirve la landing page estática, los assets y el archivo altstore.json directamente
tal como viene en el repositorio (actualizado por los workflows de GitHub Actions).
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("altstore-server")

BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = BASE_DIR / "altstore.json"

app = FastAPI(
    title="UDYAT APPS Server",
    description="Servidor de landing y fuente de aplicaciones para AltStore / SideStore.",
    version="1.0.0",
)

# Permitir CORS para consultas desde cualquier origen (SideStore, webs, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_source_json() -> Dict[str, Any]:
    if not JSON_FILE.exists():
        raise FileNotFoundError(f"No existe el archivo {JSON_FILE}")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# --- RUTAS DE API ---

@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/apps", tags=["API"])
def get_apps():
    """Retorna la lista de apps registradas en altstore.json."""
    data = load_source_json()
    return {
        "sourceName": data.get("name"),
        "totalApps": len(data.get("apps", [])),
        "apps": [
            {
                "name": a.get("name"),
                "bundleIdentifier": a.get("bundleIdentifier"),
                "latestVersion": a.get("versions", [{}])[0].get("version") if a.get("versions") else a.get("version")
            }
            for a in data.get("apps", [])
        ]
    }

# --- RUTA DE FUENTE DE ALTSTORE (SIRVE EL JSON DIRECTO) ---

@app.get("/altstore.json", tags=["Fuente"])
def serve_altstore_json():
    """
    Sirve el archivo altstore.json directamente con encabezados de no-cache
    para que AltStore/SideStore siempre descarguen la versión más reciente.
    """
    if not JSON_FILE.exists():
        raise HTTPException(status_code=404, detail="altstore.json no encontrado")
    return FileResponse(
        path=JSON_FILE,
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# --- WEB Y ARCHIVOS ESTÁTICOS ---

@app.get("/", tags=["Web"])
def serve_index():
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html no encontrado")
    return FileResponse(index_path, media_type="text/html")

assets_path = BASE_DIR / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

apps_path = BASE_DIR / "apps"
if apps_path.exists():
    app.mount("/apps", StaticFiles(directory=str(apps_path)), name="apps")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 80))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
