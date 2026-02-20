from __future__ import annotations

import logging
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from .config import Settings, Rule
from .gmail_api import iter_message_ids, trash_message, batch_delete

log = logging.getLogger(__name__)
console = Console()

@dataclass
class RuleResult:
    rule: Rule
    ids: list[str]

def plan(service, settings: Settings) -> list[RuleResult]:
    results: list[RuleResult] = []
    for rule in settings.rules:
        ids = list(
            iter_message_ids(
                service=service,
                user_id=settings.app.user_id,
                query=rule.query,
                include_spam_trash=rule.include_spam_trash,
                page_size=settings.app.page_size,
                max_total=rule.max_results,
            )
        )
        results.append(RuleResult(rule=rule, ids=ids))
    return results

def print_plan(results: list[RuleResult]) -> None:
    t = Table(title="Plano (o que seria afetado)")
    t.add_column("Regra")
    t.add_column("Ação")
    t.add_column("Qtd mensagens", justify="right")

    total = 0
    for r in results:
        t.add_row(r.rule.name, r.rule.action, str(len(r.ids)))
        total += len(r.ids)

    t.caption = f"Total: {total}"
    console.print(t)

def apply(service, settings: Settings, results: list[RuleResult], force: bool = False) -> None:
    if settings.app.dry_run and not force:
        console.print("[yellow]DRY-RUN ativo. Nada foi alterado.[/yellow]")
        return

    for rr in results:
        if not rr.ids:
            continue

        console.print(f"\n[bold]{rr.rule.name}[/bold] | ação={rr.rule.action} | msgs={len(rr.ids)}")

        if rr.rule.action == "TRASH":
            for i, mid in enumerate(rr.ids, start=1):
                trash_message(service, settings.app.user_id, mid)
                if i % 100 == 0:
                    console.print(f"  ... {i}/{len(rr.ids)} movidas pro lixo")
            console.print(f"[green]OK[/green] {len(rr.ids)} movidas para TRASH.")

        elif rr.rule.action == "DELETE":
            # AVISO: delete é irreversível e pode exigir escopo mais amplo :contentReference[oaicite:8]{index=8}
            # Aqui fazemos em lotes por segurança.
            chunk = 500
            for start in range(0, len(rr.ids), chunk):
                batch = rr.ids[start : start + chunk]
                batch_delete(service, settings.app.user_id, batch)
            console.print(f"[red]OK[/red] {len(rr.ids)} deletadas PERMANENTEMENTE.")