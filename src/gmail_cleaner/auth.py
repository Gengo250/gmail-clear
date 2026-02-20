from __future__ import annotations

from pathlib import Path
from typing import Sequence

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Escopo mínimo seguro pra listar e mover pro lixo :contentReference[oaicite:4]{index=4}
DEFAULT_SCOPES: Sequence[str] = ("https://www.googleapis.com/auth/gmail.modify",)

def get_credentials(
    credentials_path: str,
    token_path: str,
    scopes: Sequence[str] = DEFAULT_SCOPES,
) -> Credentials:
    cred_file = Path(credentials_path)
    token_file = Path(token_path)

    creds: Credentials | None = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes=scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), scopes=scopes)
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json(), encoding="utf-8")

    return creds