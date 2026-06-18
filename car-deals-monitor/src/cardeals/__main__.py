"""Punto de entrada CLI: ``python -m cardeals``."""
from __future__ import annotations

import argparse
import logging
import sys

from .config import AppConfig
from .runner import run
from .scrapers import SCRAPERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cardeals",
        description="Monitoriza ofertas de coches y envía emails con las novedades.",
    )
    parser.add_argument(
        "-c", "--config", default="config.yaml",
        help="Ruta al fichero de configuración YAML (por defecto config.yaml).",
    )
    parser.add_argument(
        "--state", default=None,
        help="Ruta al fichero de estado (sobreescribe config/entorno).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="No envía email ni guarda estado; solo muestra qué se enviaría.",
    )
    parser.add_argument(
        "--list-portals", action="store_true",
        help="Lista los portales disponibles y sale.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Logging detallado.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.list_portals:
        print("Portales disponibles:")
        for name in sorted(SCRAPERS):
            print(f"  - {name}")
        return 0

    config = AppConfig.load(args.config, state_path=args.state)
    new = run(config, dry_run=args.dry_run)

    total = sum(len(v) for v in new.values())
    if args.dry_run:
        for search_name, listings in new.items():
            print(f"\n== {search_name} ({len(listings)}) ==")
            for ls in listings:
                print(f"  - {ls.title} | {ls.price_str()} | {ls.url}")
        print(f"\nTotal novedades: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
