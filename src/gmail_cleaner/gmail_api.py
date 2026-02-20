from __future__ import annotations

import logging
from typing import Iterable, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

log = logging.getLogger(__name__)

def _is_retryable(err: Exception) -> bool:
    if isinstance(err, HttpError):
        status = getattr(err.resp, "status", None)
        return status in (429, 500, 502, 503, 504)
    return False

@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(5), retry=retry_if_exception(_is_retryable))
def build_gmail_service(creds):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def iter_message_ids(
    service,
    user_id: str,
    query: str,
    include_spam_trash: bool,
    page_size: int,
    max_total: int,
) -> Iterable[str]:
    # list suporta q=... e includeSpamTrash :contentReference[oaicite:5]{index=5}
    page_token = None
    got = 0

    while True:
        resp = (
            service.users()
            .messages()
            .list(
                userId=user_id,
                q=query,
                includeSpamTrash=include_spam_trash,
                maxResults=min(500, page_size),
                pageToken=page_token,
            )
            .execute()
        )

        msgs = resp.get("messages", []) or []
        for m in msgs:
            yield m["id"]
            got += 1
            if got >= max_total:
                return

        page_token = resp.get("nextPageToken")
        if not page_token:
            return

@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(5), retry=retry_if_exception(_is_retryable))
def trash_message(service, user_id: str, msg_id: str) -> None:
    # Preferir trash ao delete :contentReference[oaicite:6]{index=6}
    service.users().messages().trash(userId=user_id, id=msg_id).execute()

@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(5), retry=retry_if_exception(_is_retryable))
def batch_delete(service, user_id: str, msg_ids: List[str]) -> None:
    # batchDelete existe no recurso users.messages :contentReference[oaicite:7]{index=7}
    service.users().messages().batchDelete(userId=user_id, body={"ids": msg_ids}).execute()