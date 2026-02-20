from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lambriz_order_api")

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "config.env"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(ENV_PATH)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.yandex.ru").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_SECURE = os.getenv("SMTP_SECURE", "true").strip().lower() == "true"
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
MAIL_TO = os.getenv("MAIL_TO", SMTP_USER).strip()
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER).strip()
API_PORT = int(os.getenv("ORDER_API_PORT", os.getenv("PORT", "8080")))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*").strip() or "*"


def format_price(value: object) -> str:
    try:
        num = float(value)
        return f"{num:,.0f}".replace(",", " ")
    except Exception:
        return "0"


def build_order_email(payload: dict) -> tuple[str, str]:
    created = payload.get("createdAt") or datetime.utcnow().isoformat()
    customer = payload.get("customer") or {}
    items = payload.get("items") or []
    request_items = payload.get("requestPriceItems") or [i for i in items if i.get("isRequestPrice")]
    priced_items = payload.get("pricedItems") or [i for i in items if not i.get("isRequestPrice")]
    total_display = payload.get("totalDisplay") or f"{format_price(payload.get('total', 0))} ₽"
    request_label = "Запрос цены" if request_items else ""

    subject = f"Новая заявка №{payload.get('id', '-')}"
    lines = [
        f"Дата: {created}",
        f"Имя: {customer.get('name', '-')}",
        f"Телефон: {customer.get('phone', '-')}",
        f"Email: {customer.get('email', '-')}",
        f"Telegram ID: {customer.get('telegramUserId') or payload.get('telegramUserId') or '-'}",
        f"Способ связи: {customer.get('contactMethod', '-')}",
        f"Комментарий: {customer.get('comment', '-')}",
        "",
        "Товары с ценой:",
    ]

    if priced_items:
        for i in priced_items:
            lines.append(
                f"- {i.get('title', '-')}, арт. {i.get('sku', '-')}, "
                f"{i.get('qty', 1)} шт × {format_price(i.get('price', 0))} ₽"
            )
    else:
        lines.append("- Нет")

    lines.append("")
    lines.append("Запрос цены:")
    if request_items:
        for i in request_items:
            lines.append(f"- {i.get('title', '-')}, арт. {i.get('sku', '-')}, {i.get('qty', 1)} шт")
    else:
        lines.append("- Нет")

    lines.append("")
    lines.append(f"Итого: {total_display}{' + ' + request_label if request_label else ''}")
    text_body = "\n".join(lines)

    html = [
        "<h2>Новая заявка с Mini App</h2>",
        f"<p><b>Дата:</b> {created}</p>",
        "<h3>Контактные данные</h3>",
        f"<p><b>Имя:</b> {customer.get('name', '-')}<br>"
        f"<b>Телефон:</b> {customer.get('phone', '-')}<br>"
        f"<b>Email:</b> {customer.get('email', '-')}<br>"
        f"<b>Telegram ID:</b> {customer.get('telegramUserId') or payload.get('telegramUserId') or '-'}<br>"
        f"<b>Способ связи:</b> {customer.get('contactMethod', '-')}<br>"
        f"<b>Комментарий:</b> {customer.get('comment', '-')}</p>",
        "<h3>Товары с ценой</h3><ul>",
    ]
    if priced_items:
        for i in priced_items:
            html.append(
                "<li>"
                f"{i.get('title', '-')}, арт. {i.get('sku', '-')}, "
                f"{i.get('qty', 1)} шт × {format_price(i.get('price', 0))} ₽"
                "</li>"
            )
    else:
        html.append("<li>Нет</li>")
    html.append("</ul><h3>Запрос цены</h3><ul>")
    if request_items:
        for i in request_items:
            html.append(
                "<li>"
                f"{i.get('title', '-')}, арт. {i.get('sku', '-')}, {i.get('qty', 1)} шт"
                "</li>"
            )
    else:
        html.append("<li>Нет</li>")
    html.append("</ul>")
    html.append(f"<p><b>Итого:</b> {total_display}{' + ' + request_label if request_label else ''}</p>")
    html_body = "".join(html)
    return subject, text_body + "\n", html_body


def build_feedback_email(payload: dict) -> tuple[str, str, str]:
    created = payload.get("createdAt") or datetime.utcnow().isoformat()
    customer = payload.get("customer") or {}
    subject = "Обратная связь"
    text = (
        f"Дата: {created}\n"
        f"Имя: {customer.get('name', '-')}\n"
        f"Телефон: {customer.get('phone', '-')}\n"
        f"Email: {customer.get('email', '-')}\n"
        f"Telegram ID: {customer.get('telegramUserId') or payload.get('telegramUserId') or '-'}\n"
        f"Способ связи: {customer.get('contactMethod', '-')}\n"
        f"Комментарий: {payload.get('message', '-')}\n"
    )
    html = (
        "<h2>Обратная связь</h2>"
        f"<p><b>Дата:</b> {created}</p>"
        f"<p><b>Имя:</b> {customer.get('name', '-')}<br>"
        f"<b>Телефон:</b> {customer.get('phone', '-')}<br>"
        f"<b>Email:</b> {customer.get('email', '-')}<br>"
        f"<b>Telegram ID:</b> {customer.get('telegramUserId') or payload.get('telegramUserId') or '-'}<br>"
        f"<b>Способ связи:</b> {customer.get('contactMethod', '-')}<br>"
        f"<b>Комментарий:</b> {payload.get('message', '-')}</p>"
    )
    return subject, text, html


def send_email(subject: str, text_body: str, html_body: str) -> None:
    if not SMTP_USER or not SMTP_PASS or not MAIL_TO:
        raise RuntimeError("SMTP_USER/SMTP_PASS/MAIL_TO not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if SMTP_SECURE:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(MAIL_FROM, [MAIL_TO], msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(MAIL_FROM, [MAIL_TO], msg.as_string())


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS,GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "service": "lambriz-order-api"}).encode("utf-8"))
            return
        self.send_response(404)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api/order":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")) or 0)
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
            request_type = (payload.get("requestType") or payload.get("type") or "").strip().lower()
            if request_type == "feedback":
                subject, text_body, html_body = build_feedback_email(payload)
            else:
                subject, text_body, html_body = build_order_email(payload)

            send_email(subject, text_body, html_body)

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        except Exception as err:
            logger.exception("Order API error")
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(err)}).encode("utf-8"))


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", API_PORT), Handler)
    logger.info("Lambriz order API started on :%s", API_PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
