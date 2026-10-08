# UDYAT APPS — Fuente para SideStore / AltStore

Fuente (source) de aplicaciones para **SideStore** y **AltStore**, con:

- `altstore.json` — la source en **formato v2** (compatible con SideStore y AltStore 2).
- `index.html` — landing page con botón "Añadir a SideStore" (deep link `sidestore://`).
- `docker-compose.yml` — servidor de **anisette v3** autoalojado + servidor web opcional para el JSON.

## URLs

| Servicio | URL |
|---|---|
| Source (GitHub Pages) | `https://eljoker63.github.io/ALTSTORE/altstore.json` |
| Deep link SideStore | `sidestore://source?url=https://eljoker63.github.io/ALTSTORE/altstore.json` |
| Deep link AltStore | `altstore://source?url=https://eljoker63.github.io/ALTSTORE/altstore.json` |

## Cómo funciona (modelo de firma)

- Cada usuario firma las apps **en su propio iPhone** con **su propio Apple ID**.
- El Apple ID **nunca pasa por este servidor**. SideStore lo guarda en el keychain del dispositivo.
- SideStore refresca la firma automáticamente en segundo plano cada pocos días (con StosVPN activo).
- Lo único que necesita de un servidor son los **datos anisette**, que son anónimos.

## Servidor anisette (autoalojado)

```bash
docker compose up -d anisette
```

Tras levantarlo, los usuarios pueden configurarlo en
**SideStore → Settings → Anisette Servers → `http://<tu-servidor>:6969`**.

> Para exponerlo a Internet es recomendable ponerlo detrás de un proxy con HTTPS
> (Caddy, nginx, Cloudflare Tunnel…). El servicio `web` del compose también puede
> servir el `altstore.json` por el puerto 8080 si prefieres no depender de GitHub Pages.

## Publicar una nueva versión de una app

1. Sube el `.ipa` a la release correspondiente en GitHub.
2. Edita `altstore.json`:
   - Añade un objeto nuevo **al principio** del array `versions[]` de la app
     (la primera entrada es la que se muestra como "última versión").
   - Rellena `version`, `date`, `downloadURL` y el `size` **exacto en bytes** del ipa.
3. Haz push a `main`. GitHub Pages republica solo y los usuarios ven la
   actualización en la pestaña de la fuente.

## Límites de las cuentas Apple gratuitas

- Máximo **3 apps activas** por dispositivo.
- **10 App IDs** por semana por cuenta.
- Certificados de **7 días** (SideStore los renueva solo en segundo plano).

## Aviso

Proyecto no afiliado a Apple. Las aplicaciones pertenecen a sus respectivos desarrolladores.
