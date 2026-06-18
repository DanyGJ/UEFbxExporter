# 🚗 car-deals-monitor

Monitoriza ofertas de coches en varios portales (**Coches.net**, **AutoScout24**
y cualquier otro vía selectores CSS) y te envía un **email con las novedades**
cada vez que aparecen anuncios nuevos que encajan con tus búsquedas.

- Se ejecuta solo con **GitHub Actions** (cron), sin necesidad de servidor.
- Email vía **Gmail SMTP** (contraseña de aplicación).
- **Extensible**: añadir un portal nuevo es añadir una clase o, sin código,
  describir sus selectores CSS en el YAML.
- Deduplica entre ejecuciones para no repetir anuncios ya enviados.

---

## Cómo funciona

```
config.yaml ──▶ scrapers (cochesnet / autoscout24 / generic_html)
                      │
                      ▼
            anuncios encontrados
                      │
        SeenStore (data/seen.json)  ── filtra los ya vistos
                      │
                      ▼
        EmailNotifier (Gmail SMTP) ── email solo con novedades
```

## Uso local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml        # edita tus búsquedas
cp .env.example .env                       # rellena credenciales SMTP
export $(grep -v '^#' .env | xargs)        # carga el .env (Linux/Mac)

export PYTHONPATH=src
python -m cardeals --list-portals          # ver portales disponibles
python -m cardeals --dry-run               # prueba sin enviar email
python -m cardeals                         # ejecuta de verdad
```

## Configuración

`config.yaml` contiene la lista de búsquedas. Ejemplo mínimo:

```yaml
searches:
  - name: "BMW Serie 3 hasta 12.000€"
    portal: cochesnet
    params:
      text: "BMW Serie 3"
      price_to: 12000

  - name: "Audi A3 hasta 15.000€"
    portal: autoscout24
    params:
      url: "https://www.autoscout24.es/lst/audi/a3?priceto=15000&sort=age&desc=1"
```

Ver `config.example.yaml` para todas las opciones, incluido el scraper
`generic_html` para añadir portales como **Flexicar** solo con selectores CSS.

### Secretos (email)

Nunca se guardan en el repo. En local van en `.env`; en GitHub Actions, en los
**Secrets** del repositorio (ver más abajo). Variables:

| Variable        | Descripción                                   |
|-----------------|-----------------------------------------------|
| `SMTP_USER`     | Tu correo de Gmail                            |
| `SMTP_PASSWORD` | **Contraseña de aplicación** de Gmail (16 car.)|
| `EMAIL_TO`      | Destinatario(s), separados por comas          |
| `EMAIL_FROM`    | Remitente (por defecto = `SMTP_USER`)         |
| `SMTP_HOST`     | `smtp.gmail.com` (por defecto)                |
| `SMTP_PORT`     | `587` (por defecto)                           |

> **Gmail**: necesitas verificación en 2 pasos y una *contraseña de aplicación*
> (https://myaccount.google.com/apppasswords). No funciona con tu contraseña normal.

## Despliegue con GitHub Actions

1. Sube este proyecto a un repositorio de GitHub (ver instrucciones abajo).
2. En el repo: **Settings → Secrets and variables → Actions → New repository secret**
   y crea `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO` (y opcionalmente los demás).
3. El workflow `.github/workflows/monitor.yml` se ejecuta cada 2 horas (ajustable)
   y también puede lanzarse a mano desde la pestaña **Actions** (*Run workflow*).
4. El estado de anuncios vistos (`data/seen.json`) se commitea automáticamente
   tras cada ejecución para no repetir avisos.

## Añadir un portal nuevo

**Opción A — sin código (recomendado para empezar):** usa el portal
`generic_html` en `config.yaml` y describe los selectores CSS de las tarjetas de
resultados. Ver el ejemplo de Flexicar en `config.example.yaml`.

**Opción B — con código:** crea `src/cardeals/scrapers/miportal.py`:

```python
from ..config import SearchConfig
from ..models import Listing
from .base import Scraper, register

@register("miportal")
class MiPortalScraper(Scraper):
    def search(self, search: SearchConfig) -> list[Listing]:
        ...  # devuelve una lista de Listing
```

e impórtalo en `src/cardeals/scrapers/__init__.py`.

## Tests

```bash
PYTHONPATH=src pytest
```

## Aviso legal

Este proyecto consulta páginas/APIs públicas para uso personal. Respeta los
términos de uso de cada portal y los `robots.txt`; los retardos entre peticiones
están pensados para no sobrecargar los servidores. Los endpoints/HTML de los
portales cambian con el tiempo: si un scraper deja de devolver resultados,
actualiza el endpoint o los selectores según se indica en cada módulo.
