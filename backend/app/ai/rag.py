from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import KnowledgeArticle


def _tokens(text: str) -> set[str]:
    raw = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
    return {t for t in raw.split() if len(t) >= 3}


async def retrieve_articles(db: AsyncSession, query: str, limit: int = 3) -> list[KnowledgeArticle]:
    q = query.strip()
    if not q:
        return []

    tokens = list(_tokens(q))[:8]
    stmt = select(KnowledgeArticle).where(
        KnowledgeArticle.deleted_at.is_(None),
        KnowledgeArticle.status == "APPROVED",
    )
    result = await db.execute(stmt)
    articles = list(result.scalars().all())
    if not articles:
        return []

    scored: list[tuple[int, KnowledgeArticle]] = []
    q_tokens = _tokens(q)
    for article in articles:
        blob = " ".join(
            filter(
                None,
                [
                    article.title,
                    article.category,
                    article.problem,
                    article.symptoms,
                    article.solution,
                    " ".join(article.related_software or []),
                ],
            )
        ).lower()
        score = sum(1 for t in q_tokens if t in blob)
        qlow = q.lower()
        # Strong boost for FOM — primary pharmacy software
        if "fom" in qlow and (
            article.category.upper() == "FOM"
            or "fom" in (article.title or "").lower()
            or any("fom" in str(s).lower() for s in (article.related_software or []))
        ):
            score += 8
        for soft in ("f-apteka", "printer", "chek", "internet", "kassa", "fiscal", "smena"):
            if soft in qlow and soft in blob:
                score += 2
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [a for _, a in scored[:limit]]

    # fallback: category keyword match via SQL
    if tokens:
        like_filters = [KnowledgeArticle.title.ilike(f"%{t}%") for t in tokens[:3]]
        like_filters += [KnowledgeArticle.problem.ilike(f"%{t}%") for t in tokens[:3]]
        result = await db.execute(stmt.where(or_(*like_filters)).limit(limit))
        return list(result.scalars().all())
    return []


def format_kb_context(articles: list[KnowledgeArticle]) -> str:
    if not articles:
        return "Tasdiqlangan KB maqola topilmadi."
    parts = []
    for i, a in enumerate(articles, 1):
        steps = a.steps or []
        step_text = "\n".join(f"  - {s}" for s in steps) if steps else ""
        parts.append(
            f"[{i}] {a.title} ({a.category})\n"
            f"Muammo: {a.problem or '-'}\n"
            f"Yechim: {a.solution}\n"
            f"Qadamlar:\n{step_text}"
        )
    return "\n\n".join(parts)
