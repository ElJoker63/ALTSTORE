#!/usr/bin/env python3
"""
Script interactivo para gestionar y actualizar las versiones de las aplicaciones en altstore.json.
Permite añadir nuevas versiones o editar existentes, calculando el tamaño en bytes
a partir de archivos locales, sufijos (MB, KB), detección por URL o entrada manual.
"""

import os
import sys
import json
import shutil
import re
from datetime import datetime
import urllib.request

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "altstore.json")

def load_json(path):
    if not os.path.exists(path):
        print(f"\n[!] Error: No se encontró el archivo: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    # Guardar copia de seguridad
    backup_path = f"{path}.bak"
    shutil.copyfile(path, backup_path)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"\n[OK] ¡Archivo guardado con éxito! (Backup previo creado en: {os.path.basename(backup_path)})")

def parse_size_input(val_str, download_url=""):
    """
    Interpreta el tamaño introducido por el usuario:
    - Ruta a un archivo .ipa local (ej: C:\apps\app.ipa)
    - Con sufijo (ej: 9.1mb, 9.1m, 9100kb, 9100k)
    - Número entero en bytes (ej: 9602019)
    - Vacío o 'auto' para intentar obtenerlo de download_url mediante Content-Length
    """
    val = val_str.strip()
    
    # Si ingresó la ruta de un archivo local
    cleaned_path = val.strip("\"'")
    if os.path.isfile(cleaned_path):
        size_bytes = os.path.getsize(cleaned_path)
        print(f" -> Archivo detectado: {os.path.basename(cleaned_path)} ({size_bytes:,} bytes / {size_bytes/(1024*1024):.2f} MB)")
        return size_bytes

    # Si quiere autodetectar por URL
    if val.lower() in ("auto", "url", "head") and download_url:
        detected = get_url_content_length(download_url)
        if detected is not None:
            return detected
        print(" -> No se pudo detectar por URL. Por favor ingresa el valor manual.")
        return None

    # Si usó sufijo MB / MiB
    match_mb = re.match(r"^([\d.]+)\s*(mb|m|mib)$", val, re.IGNORECASE)
    if match_mb:
        num = float(match_mb.group(1))
        # Base binaria 1024 * 1024
        size_bytes = int(round(num * 1024 * 1024))
        print(f" -> Convertido {num} MB a {size_bytes:,} bytes")
        return size_bytes

    # Si usó sufijo KB / KiB
    match_kb = re.match(r"^([\d.]+)\s*(kb|k|kib)$", val, re.IGNORECASE)
    if match_kb:
        num = float(match_kb.group(1))
        size_bytes = int(round(num * 1024))
        print(f" -> Convertido {num} KB a {size_bytes:,} bytes")
        return size_bytes

    # Si es un número entero de bytes
    if re.match(r"^\d+$", val):
        size_bytes = int(val)
        print(f" -> {size_bytes:,} bytes ({size_bytes/(1024*1024):.2f} MB)")
        return size_bytes

    return None

def get_url_content_length(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            cl = resp.headers.get("Content-Length")
            if cl and cl.isdigit():
                cl_bytes = int(cl)
                print(f" -> Tamaño detectado del servidor: {cl_bytes:,} bytes ({cl_bytes/(1024*1024):.2f} MB)")
                return cl_bytes
    except Exception as e:
        print(f" -> Advertencia: No se pudo consultar el servidor ({e})")
    return None

def prompt(message, default=None):
    if default is not None:
        raw = input(f"{message} [{default}]: ").strip()
        return raw if raw else default
    return input(f"{message}: ").strip()

def prompt_size(default_bytes=0, download_url=""):
    while True:
        default_str = str(default_bytes) if default_bytes else ""
        if default_bytes > 0:
            prompt_label = f"Tamaño (ej: '9.1mb', bytes directos, ruta de archivo .ipa o 'auto')"
            val = prompt(prompt_label, default=default_str)
        else:
            prompt_label = "Tamaño (ej: '9.1mb', bytes directos, ruta de archivo .ipa o 'auto')"
            val = prompt(prompt_label)

        if not val and default_bytes:
            return default_bytes

        res = parse_size_input(val, download_url)
        if res is not None:
            return res
        print("[!] Formato no válido. Puedes escribir: '9.1mb', '9542042', la ruta de tu .ipa o 'auto'.")

def choose_app(apps):
    print("\n" + "="*50)
    print(" APLICACIONES DISPONIBLES EN ALTSTORE.JSON ")
    print("="*50)
    for idx, app in enumerate(apps, 1):
        latest = app.get("versions", [{}])[0].get("version", "N/A") if app.get("versions") else "Sin versiones"
        print(f"  {idx}) {app.get('name', 'Sin nombre')} ({app.get('bundleIdentifier')}) - [Última ver: {latest}]")
    print("  0) Salir")
    print("="*50)

    while True:
        choice = input("Selecciona una app por su número: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(apps):
            return apps[int(choice) - 1]
        print("[!] Opción inválida.")

def manage_app(app):
    name = app.get("name", "App")
    versions = app.setdefault("versions", [])

    print(f"\n--- Gestionando: {name} ---")
    print("1) Agregar NUEVA versión (se colocará como la más reciente)")
    print("2) Editar la ÚLTIMA versión existente")
    print("3) Ver historial de versiones")
    print("0) Volver al menú principal")

    opt = input("Elige una opción: ").strip()

    if opt == "1":
        latest_ver = versions[0] if versions else {}
        print(f"\n[+] Agregando nueva versión para {name}")
        
        ver = prompt("Número de versión (ej: 1.0.1)")
        while not ver:
            print("[!] La versión no puede estar vacía.")
            ver = prompt("Número de versión")

        today = datetime.now().strftime("%Y-%m-%d")
        date_str = prompt("Fecha (YYYY-MM-DD)", default=today)

        desc = prompt("Descripción / Novedades de la versión", default="Correcciones y mejoras.")

        def_url = latest_ver.get("downloadURL", "")
        download_url = prompt("URL de descarga (.ipa)", default=def_url)

        size_bytes = prompt_size(default_bytes=latest_ver.get("size", 0), download_url=download_url)

        def_min_os = latest_ver.get("minOSVersion", "14.0")
        min_os = prompt("Versión mínima de iOS", default=def_min_os)

        new_entry = {
            "version": ver,
            "date": date_str,
            "localizedDescription": desc,
            "downloadURL": download_url,
            "size": size_bytes,
            "minOSVersion": min_os
        }

        print("\nNueva versión a agregar:")
        print(json.dumps(new_entry, indent=2, ensure_ascii=False))
        confirm = input("\n¿Confirmar y agregar? (s/n) [s]: ").strip().lower()
        if confirm in ("", "s", "si", "y", "yes"):
            versions.insert(0, new_entry)
            return True

    elif opt == "2":
        if not versions:
            print("[!] No hay versiones para editar.")
            return False
        
        target = versions[0]
        print(f"\n[*] Editando versión {target.get('version')}:")

        ver = prompt("Versión", default=target.get("version"))
        date_str = prompt("Fecha (YYYY-MM-DD)", default=target.get("date", datetime.now().strftime("%Y-%m-%d")))
        desc = prompt("Descripción", default=target.get("localizedDescription", ""))
        download_url = prompt("URL de descarga", default=target.get("downloadURL", ""))
        size_bytes = prompt_size(default_bytes=target.get("size", 0), download_url=download_url)
        min_os = prompt("Versión mínima de iOS", default=target.get("minOSVersion", "14.0"))

        target["version"] = ver
        target["date"] = date_str
        target["localizedDescription"] = desc
        target["downloadURL"] = download_url
        target["size"] = size_bytes
        target["minOSVersion"] = min_os

        print("\nVersión actualizada:")
        print(json.dumps(target, indent=2, ensure_ascii=False))
        confirm = input("\n¿Confirmar cambios? (s/n) [s]: ").strip().lower()
        return confirm in ("", "s", "si", "y", "yes")

    elif opt == "3":
        print(f"\n--- Historial de {name} ({len(versions)} versiones) ---")
        for i, v in enumerate(versions, 1):
            s_mb = v.get('size', 0) / (1024 * 1024)
            print(f" {i}. v{v.get('version')} ({v.get('date')}) - {v.get('size', 0):,} bytes ({s_mb:.2f} MB)")
            print(f"    Desc: {v.get('localizedDescription')}")
            print(f"    URL:  {v.get('downloadURL')}")
        input("\nPresiona Enter para continuar...")
        return False

    return False

def main():
    print("==================================================")
    print("   GESTOR DE VERSIONES DE ALTSTORE / SIDESTORE    ")
    print("==================================================")
    
    data = load_json(JSON_PATH)
    apps = data.get("apps", [])
    
    if not apps:
        print("[!] No se encontraron aplicaciones en la clave 'apps' del JSON.")
        return

    while True:
        app = choose_app(apps)
        if app is None:
            print("\n¡Hasta luego!")
            break
        
        modified = manage_app(app)
        if modified:
            save_json(JSON_PATH, data)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
