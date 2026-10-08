# UDYAT APPS — Fuente para SideStore / AltStore

Fuente (source) de aplicaciones para **SideStore** y **AltStore**, con:

- `altstore.json` — la source en **formato v2** (compatible con SideStore y AltStore 2).
- `index.html` — landing page con botón "Añadir a SideStore" (deep link `sidestore://`).
- `Dockerfile` — sirve la landing + el JSON con nginx (despliegue en Coolify).
- `docker-compose.yml` — alternativa todo-en-uno para VPS sin Coolify.

## URLs de producción (Coolify)

| Servicio | Dominio | Puerto interno |
|---|---|---|
| Tienda (landing + source) | `https://sidestore.udyat.site` | 80 |
| Anisette (firma/refresco) | `https://anisette.udyat.site` | 6969 |

| Uso | URL |
|---|---|
| Source | `https://sidestore.udyat.site/altstore.json` |
| Deep link SideStore | `sidestore://source?url=https://sidestore.udyat.site/altstore.json` |
| Deep link AltStore | `altstore://source?url=https://sidestore.udyat.site/altstore.json` |

## Despliegue en Coolify

### 1. Tienda (este repo)

- Tipo: **Dockerfile** (el de este repo, nginx sirviendo la raíz).
- Dominio: `https://sidestore.udyat.site` → puerto **80**.
- Activa el **webhook de GitHub** en Coolify para que cada push a `main`
  redespliegue solo (así "cambiar el JSON" = "la tienda se actualiza").

### 2. Anisette

- Tipo: **Public Repository** → `https://github.com/Dadoum/anisette-v3-server`
  (su Dockerfile ya viene incluido, Coolify lo construye tal cual).
- Dominio: `https://anisette.udyat.site` → puerto **6969**.
- Los usuarios lo ponen en **SideStore → Settings → Anisette Servers**.

> DNS: ambos subdominios (`sidestore.` y `anisette.`) deben apuntar
> con registros A a la IP del servidor Coolify.

## Cómo funciona (modelo de firma)

- Cada usuario firma las apps **en su propio iPhone** con **su propio Apple ID**.
- El Apple ID **nunca pasa por estos servidores**. SideStore lo guarda en el
  keychain del dispositivo.
- SideStore refresca la firma automáticamente en segundo plano cada pocos días
  (con StosVPN activo).
- El servidor anisette solo genera **datos anisette anónimos** que Apple exige
  en cada firma/refresco. No almacena ni recibe credenciales.

## Publicar una nueva versión de una app

1. Sube el `.ipa` a la release correspondiente en GitHub.
2. Edita `altstore.json`:
   - Añade un objeto nuevo **al principio** del array `versions[]` de la app
     (la primera entrada es la que se muestra como "última versión").
   - Rellena `version`, `date`, `downloadURL` y el `size` **exacto en bytes** del ipa.
3. Haz push a `main`; Coolify redespliega por webhook y los usuarios ven la
   actualización en la pestaña de la fuente.

## Límites de las cuentas Apple gratuitas

- Máximo **3 apps activas** por dispositivo.
- **10 App IDs** por semana por cuenta.
- Certificados de **7 días** (SideStore los renueva solo en segundo plano).

## Aviso

Proyecto no afiliado a Apple. Las aplicaciones pertenecen a sus respectivos desarrolladores.
