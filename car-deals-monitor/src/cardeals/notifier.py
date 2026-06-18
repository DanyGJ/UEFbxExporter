"""Envío de emails con las novedades vía SMTP (por defecto Gmail)."""
from __future__ import annotations

import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import EmailConfig
from .models import Listing

log = logging.getLogger(__name__)


def build_html(grouped: dict[str, list[Listing]]) -> str:
    """Construye el cuerpo HTML del email agrupando por nombre de búsqueda."""
    total = sum(len(v) for v in grouped.values())
    parts: list[str] = [
        "<html><body style=\"font-family:Arial,Helvetica,sans-serif;color:#222\">",
        f"<h2>🚗 {total} coche(s) nuevo(s)</h2>",
    ]
    for search_name, listings in grouped.items():
        if not listings:
            continue
        parts.append(f"<h3 style=\"margin-top:24px\">{html.escape(search_name)} "
                     f"<span style=\"color:#888;font-weight:normal\">({len(listings)})</span></h3>")
        for ls in listings:
            specs = " · ".join(
                s for s in [
                    ls.price_str(),
                    f"{ls.year}" if ls.year else None,
                    f"{ls.km:,} km".replace(",", ".") if ls.km else None,
                    ls.fuel,
                    ls.location,
                ] if s
            )
            img = (
                f'<img src="{html.escape(ls.image)}" alt="" '
                'style="width:140px;border-radius:6px;margin-right:12px;vertical-align:top">'
                if ls.image else ""
            )
            parts.append(
                '<div style="margin:12px 0;padding:10px;border:1px solid #eee;border-radius:8px">'
                f'{img}'
                '<div style="display:inline-block;vertical-align:top;max-width:420px">'
                f'<a href="{html.escape(ls.url)}" style="font-size:15px;font-weight:bold;'
                f'color:#1a73e8;text-decoration:none">{html.escape(ls.title)}</a>'
                f'<div style="color:#444;margin-top:4px">{html.escape(specs)}</div>'
                f'<div style="color:#999;font-size:12px;margin-top:2px">{html.escape(ls.portal)}</div>'
                "</div></div>"
            )
    parts.append("<hr><p style=\"color:#aaa;font-size:12px\">Enviado por car-deals-monitor</p>")
    parts.append("</body></html>")
    return "".join(parts)


def build_text(grouped: dict[str, list[Listing]]) -> str:
    lines: list[str] = []
    for search_name, listings in grouped.items():
        if not listings:
            continue
        lines.append(f"== {search_name} ({len(listings)}) ==")
        for ls in listings:
            lines.append(f"- {ls.title} | {ls.price_str()} | {ls.url}")
        lines.append("")
    return "\n".join(lines)


class EmailNotifier:
    def __init__(self, config: EmailConfig):
        self.config = config

    def send(self, grouped: dict[str, list[Listing]]) -> None:
        total = sum(len(v) for v in grouped.values())
        if total == 0:
            log.info("No hay novedades; no se envía email.")
            return
        if not self.config.is_complete:
            raise RuntimeError(
                "Configuración de email incompleta. Define SMTP_USER, SMTP_PASSWORD y EMAIL_TO."
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚗 {total} coche(s) nuevo(s) — car-deals-monitor"
        msg["From"] = self.config.sender
        msg["To"] = ", ".join(self.config.recipients)
        msg.attach(MIMEText(build_text(grouped), "plain", "utf-8"))
        msg.attach(MIMEText(build_html(grouped), "html", "utf-8"))

        log.info("Enviando email a %s vía %s:%s",
                 self.config.recipients, self.config.smtp_host, self.config.smtp_port)
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(self.config.user, self.config.password)
            server.sendmail(self.config.sender, self.config.recipients, msg.as_string())
        log.info("Email enviado correctamente.")
