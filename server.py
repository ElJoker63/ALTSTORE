#!/usr/bin/env python3
"""
Servidor Web + API Webhook para UDYAT APPS (AltStore / SideStore source).
Sirve la landing page estática, los assets, el archivo altstore.json y
expone un webhook para recibir lanzamientos (releases) de GitHub y
actualizar las aplicaciones automáticamente.
"""

import os
import sys
import json
import hmac
import hashlib
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, HTTPException, Header, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("altstore-server")

BASE_DIR = Path(__file__).resolve().parent

# Directorio de datos (configurable para volumenes persistentes de Docker)
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
JSON_FILE = DATA_DIR / "altstore.json"

# Inicializar altstore.json si se usa un volumen persistente nuevo
if not JSON_FILE.exists():
    fallback_json = BASE_DIR / "altstore.json"
    if fallback_json.exists():
        logger.info(f"Copiando altstore.json inicial a {JSON_FILE}")
        shutil.copyfile(fallback_json, JSON_FILE)

# Secret opcional para verificar que los webhooks vienen de GitHub
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode("utf-8")

app = FastAPI(
    title="UDYAT APPS Server",
    description="Servidor de landing y fuente de aplicaciones para AltStore / SideStore con Webhook automático.",
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

def save_source_json(data: Dict[str, Any]) -> None:
    # Backup de seguridad antes de sobreescribir
    backup_file = JSON_FILE.with_suffix(".json.bak")
    try:
        shutil.copyfile(JSON_FILE, backup_file)
    except Exception as e:
        logger.warning(f"No se pudo crear backup de {JSON_FILE}: {e}")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    logger.info("altstore.json actualizado exitosamente.")

def verify_github_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """Valida la firma HMAC SHA-256 enviada por GitHub en X-Hub-Signature-256."""
    if not WEBHOOK_SECRET:
        # Si no se configuró secret en las variables de entorno, se permite la petición
        return True
    if not signature_header:
        return False
    
    hash_type, signature = signature_header.split("=", 1) if "=" in signature_header else ("", "")
    if hash_type != "sha256":
        return False

    mac = hmac.new(WEBHOOK_SECRET, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def match_app_for_asset(apps: List[Dict[str, Any]], asset_name: str, repo_name: str) -> Optional[Dict[str, Any]]:
    """
    Identifica qué app de altstore.json corresponde al archivo .ipa de la release.
    Usa coincidencias por:
    1. Nombre de archivo exacto en downloadURL existente
    2. Nombre del asset contenido en el bundleIdentifier o name
    3. Nombre del repositorio contenido en bundleIdentifier o name
    """
    clean_asset = asset_name.lower().replace(".ipa", "").replace("-", "").replace("_", "")
    clean_repo = repo_name.lower().replace("-", "").replace("_", "")

    # 1. Coincidencia con downloadURL previo
    for app_item in apps:
        for ver in app_item.get("versions", []):
            url = ver.get("downloadURL", "").lower()
            if asset_name.lower() in url:
                return app_item

    # 2. Coincidencia con nombre o bundleIdentifier
    for app_item in apps:
        bundle = app_item.get("bundleIdentifier", "").lower().replace("-", "").replace("_", "").replace(".", "")
        name = app_item.get("name", "").lower().replace("-", "").replace("_", "").replace(" ", "")
        
        if clean_asset in bundle or clean_asset in name or name in clean_asset:
            return app_item

    # 3. Coincidencia con el nombre del repositorio
    for app_item in apps:
        bundle = app_item.get("bundleIdentifier", "").lower().replace("-", "").replace("_", "").replace(".", "")
        name = app_item.get("name", "").lower().replace("-", "").replace("_", "").replace(" ", "")
        if clean_repo in bundle or clean_repo in name or name in clean_repo:
            return app_item

    return None

# --- RUTAS DE API Y WEBHOOK ---

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
                "latestVersion": a.get("versions", [{}])[0].get("version") if a.get("versions") else None
            }
            for a in data.get("apps", [])
        ]
    }

@app.post("/api/webhook/github", tags=["Webhook"])
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Endpoint de recepción de Webhooks de GitHub.
    Procesa el evento 'release' cuando se publica una nueva release.
    """
    body_bytes = await request.body()

    # Validar firma de seguridad
    if WEBHOOK_SECRET and not verify_github_signature(body_bytes, x_hub_signature_256):
        logger.warning("Firma de Webhook de GitHub no válida o no autorizada.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma X-Hub-Signature-256 no válida."
        )

    # Evento ping de GitHub al crear el webhook
    if x_github_event == "ping":
        logger.info("Ping recibido de GitHub Webhook.")
        return {"message": "pong", "status": "active"}

    if x_github_event != "release":
        logger.info(f"Evento ignorado: {x_github_event}")
        return {"message": f"Evento '{x_github_event}' ignorado. Solo se procesa 'release'."}

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON mal formado: {e}")

    action = payload.get("action")
    if action not in ("published", "created", "released"):
        return {"message": f"Acción '{action}' ignorada. Se espera 'published'."}

    release = payload.get("release", {})
    repo = payload.get("repository", {})
    repo_name = repo.get("name", "")
    tag_name = release.get("tag_name", "").strip()
    clean_version = tag_name.lstrip("vV")
    release_notes = release.get("body", "").strip() or f"Lanzamiento de versión {clean_version}"
    published_at = release.get("published_at") or datetime.utcnow().isoformat()
    release_date = published_at[:10]  # YYYY-MM-DD

    assets = release.get("assets", [])
    ipa_assets = [a for a in assets if a.get("name", "").lower().endswith(".ipa")]

    if not ipa_assets:
        logger.warning(f"La release {tag_name} en {repo_name} no contiene ningún archivo .ipa")
        return {
            "status": "skipped",
            "message": "No se encontraron archivos .ipa en los assets de la release."
        }

    source_data = load_source_json()
    apps = source_data.get("apps", [])
    updated_apps = []

    for asset in ipa_assets:
        asset_name = asset.get("name", "")
        download_url = asset.get("browser_download_url", "")
        size_bytes = asset.get("size", 0)

        target_app = match_app_for_asset(apps, asset_name, repo_name)
        if not target_app:
            logger.warning(f"No se encontró ninguna app coincidente para el asset: {asset_name} ({repo_name})")
            continue

        versions = target_app.setdefault("versions", [])
        
        # Comprobar si la versión ya existe
        existing_version = next((v for v in versions if v.get("version") == clean_version), None)
        
        if existing_version:
            # Actualizar la versión existente
            existing_version["date"] = release_date
            existing_version["localizedDescription"] = release_notes
            existing_version["downloadURL"] = download_url
            existing_version["size"] = size_bytes
            logger.info(f"Actualizada versión existente {clean_version} de {target_app.get('name')}")
        else:
            # Insertar como la más reciente al principio
            min_os = versions[0].get("minOSVersion", "14.0") if versions else "14.0"
            new_version_entry = {
                "version": clean_version,
                "date": release_date,
                "localizedDescription": release_notes,
                "downloadURL": download_url,
                "size": size_bytes,
                "minOSVersion": min_os,
            }
            versions.insert(0, new_version_entry)
            logger.info(f"Agregada nueva versión {clean_version} a {target_app.get('name')} con tamaño {size_bytes:,} bytes")

        updated_apps.append({
            "appName": target_app.get("name"),
            "bundleIdentifier": target_app.get("bundleIdentifier"),
            "version": clean_version,
            "size": size_bytes,
            "downloadURL": download_url
        })

    if updated_apps:
        save_source_json(source_data)
        return {
            "status": "success",
            "updatedApps": updated_apps
        }

    return {
        "status": "no_match",
        "message": "Se encontraron archivos .ipa pero no coincidieron con ninguna app en altstore.json."
    }

# --- RUTAS DE FUENTE DE ALTSTORE Y ARCHIVOS ESTÁTICOS ---

@app.get("/altstore.json", tags=["Fuente"])
def serve_altstore_json():
    """
    Sirve el archivo altstore.json con encabezados de no-cache
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

@app.get("/", tags=["Web"])
def serve_index():
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html no encontrado")
    return FileResponse(index_path, media_type="text/html")

# Montar carpetas estáticas: assets/ y apps/
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
