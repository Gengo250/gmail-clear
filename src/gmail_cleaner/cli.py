from __future__ import annotations

import argparse
import logging

from .log import setup_logging
from .config import load_settings
from .auth import get_credentials, DEFAULT_SCOPES
from .gmail_api import build_gmail_service
from .cleaner import plan, print_plan, apply

log = logging.getLogger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(prog="gmail-cleaner")
    parser.add_argument("--config", default="config/rules.yaml", help="Caminho do YAML de regras")
    parser.add_argument("--log-level", default="INFO", help="INFO, DEBUG, ...")

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth", help="Faz login OAuth e gera token.json")
    sub.add_parser("plan", help="Mostra o que seria afetado (dry-run)")

    runp = sub.add_parser("run", help="Executa as regras")
    runp.add_argument("--apply", action="store_true", help="Aplica de verdade (se não, só simula)")

    args = parser.parse_args()
    setup_logging(args.log_level)

    settings = load_settings(args.config)

    creds = get_credentials(
        credentials_path=settings.app.credentials_path,
        token_path=settings.app.token_path,
        scopes=DEFAULT_SCOPES,
    )
    service = build_gmail_service(creds)

    if args.cmd == "auth":
        print("Autenticação OK. Token salvo.")
        return

    results = plan(service, settings)
    print_plan(results)

    if args.cmd == "plan":
        return

    # run
    force = bool(args.apply)
    apply(service, settings, results, force=force)