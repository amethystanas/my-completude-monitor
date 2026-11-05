"""
Completude new-student monitor.

Polls the Completude teacher API for tutoring offers and emails you whenever
a NEW offer appears within DISTANCE_THRESHOLD_KM of your address.

Secrets (login, email) are read ONLY from environment variables:
  - on GitHub Actions they come from repository Secrets
  - locally, put them in a `.env` file next to this script (it's gitignored)

The login token is kept in memory only, so it never gets written to the repo.
"""

import json
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText

import requests

import config

BASE = "https://sic.internetude.fr/Api/ProfesseurCompletude"
LOGIN_URL = f"{BASE}/TokenAuth"
SEARCH_URL = f"{BASE}/cap/search"

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, config.STATE_FILE)

BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://professeur.completude.com",
    "Referer": "https://professeur.completude.com/",
}


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

def load_dotenv(path: str) -> None:
    """Minimal .env loader (KEY=value per line) for local runs. No dependency."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"[ERROR] Missing setting {name}. Set it as a GitHub Secret or in .env")
    return value


load_dotenv(os.path.join(HERE, ".env"))

COMPLETUDE_USERNAME = require_env("COMPLETUDE_USERNAME")
COMPLETUDE_PASSWORD = require_env("COMPLETUDE_PASSWORD")
SMTP_USERNAME = require_env("SMTP_USERNAME")
SMTP_APP_PASSWORD = require_env("SMTP_APP_PASSWORD")
EMAIL_FROM = os.environ.get("EMAIL_FROM") or SMTP_USERNAME
EMAIL_TO = os.environ.get("EMAIL_TO") or SMTP_USERNAME


# --------------------------------------------------------------------------
# State (IDs of offers already handled)
# --------------------------------------------------------------------------

def load_seen_ids() -> set:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def save_seen_ids(seen_ids: set) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(seen_ids), f)


# --------------------------------------------------------------------------
# Completude API
# --------------------------------------------------------------------------

def login() -> str:
    resp = requests.post(
        LOGIN_URL,
        data={
            "username": COMPLETUDE_USERNAME,
            "password": COMPLETUDE_PASSWORD,
            "grant_type": "password",
        },
        headers={
            **BROWSER_HEADERS,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        timeout=20,
    )
    if resp.status_code != 200:
        sys.exit(f"[ERROR] Login failed (HTTP {resp.status_code}). Check username/password.")
    return resp.json()["access_token"]


def fetch_offers(token: str) -> list:
    payload = {
        "MapBox": config.MAP_BOX,
        "SessionRecherche": {**config.SESSION_RECHERCHE, "IdAdresse": config.ID_ADRESSE},
    }
    resp = requests.post(
        SEARCH_URL,
        json=payload,
        headers={**BROWSER_HEADERS, "Authorization": f"Bearer {token}"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("Demandes", []) or []


# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------

def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=30) as server:
        server.login(SMTP_USERNAME, SMTP_APP_PASSWORD)
        server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())


def send_email_with_retry(subject: str, body: str, attempts: int = 3) -> bool:
    for attempt in range(1, attempts + 1):
        try:
            send_email(subject, body)
            return True
        except Exception as e:  # noqa: BLE001 — report any SMTP/network failure
            print(f"[WARN] Email attempt {attempt}/{attempts} failed: {e}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(5)
    return False


def format_message(offer: dict) -> str:
    return (
        f"Nouvel élève proche ({offer['Distance']:.1f} km) !\n\n"
        f"Ville      : {offer.get('Ville', '?')}\n"
        f"Niveau     : {offer.get('LibelleCombinaison', '?')}\n"
        f"Matière    : {offer.get('LibelleMatiere', '?')}\n"
        f"Fréquence  : {offer.get('LibelleFrequence', '?')} {offer.get('LibelleDuree', '')}\n"
        f"Prix       : {offer.get('DetailPrix', '')}\n"
        f"Réf.       : {offer.get('IdDemande')}\n\n"
        f"https://professeur.completude.com/"
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    first_run = not os.path.exists(STATE_PATH)
    seen_ids = load_seen_ids()

    token = login()
    offers = fetch_offers(token)

    nearby_new = [
        o for o in offers
        if o.get("IdDemande") not in seen_ids
        and o.get("Distance", 999) <= config.DISTANCE_THRESHOLD_KM
    ]
    pending = {o["IdDemande"] for o in nearby_new}

    # Everything else (far away, or already handled) is marked seen right away.
    seen_ids.update(o["IdDemande"] for o in offers if o.get("IdDemande") not in pending)

    if first_run and config.SILENT_FIRST_RUN:
        # First run: don't email you about every offer that already exists.
        seen_ids.update(pending)
        save_seen_ids(seen_ids)
        print(f"[{now}] First run: recorded {len(offers)} existing offers, no emails sent.")
        return

    save_seen_ids(seen_ids)

    if not nearby_new:
        print(f"[{now}] No new nearby offers ({len(offers)} offers in the area).")
        return

    for offer in nearby_new:
        body = format_message(offer)
        subject = f"Nouvel élève : {offer.get('Ville', '?')} ({offer['Distance']:.1f} km)"
        print(f"[{now}] NEW NEARBY OFFER\n{body}\n")
        if send_email_with_retry(subject, body):
            seen_ids.add(offer["IdDemande"])
            save_seen_ids(seen_ids)  # only mark seen once the email really went out
        else:
            print(f"[{now}] Email failed for {offer['IdDemande']}, will retry next run.",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
