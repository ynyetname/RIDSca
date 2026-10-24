import json
import math
import re
from .config import ROOT
from .guardrails import has_injection
from .schema import Reference, Check


def tokens(text):
    return re.findall(r"\w+", text.casefold())


def bm25(query, documents):
    """Small dependency-free BM25 implementation for the bundled reference corpus."""
    corpus = [tokens(d) for d in documents]
    q = set(tokens(query))
    n = len(corpus)
    avg = sum(map(len, corpus)) / max(n, 1) or 1
    scores = []
    for doc in corpus:
        score = 0.0
        for word in q:
            df = sum(word in d for d in corpus)
            freq = doc.count(word)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            score += idf * (freq * 2.5) / (freq + 1.5 * (0.25 + 0.75 * len(doc) / avg))
        scores.append(score)
    return scores


class Retriever:
    def __init__(self, models, path=None):
        self.models = models
        path = path or ROOT / "data" / "advisories.json"
        self.docs = [Reference.model_validate(d) for d in json.loads(path.read_text(encoding="utf-8"))]
        self.dense = None

    def search(self, query):
        checks = []
        # Documents are operator-curated, never uploaded into the trusted reference corpus.
        safe = [d for d in self.docs if not has_injection(d.text)]
        if not safe or not query.strip():
            return [], [
                Check(
                    component="Retrieval", status="partial", detail="No usable query or trusted references."
                )
            ]
        scores = bm25(query, [d.text + " " + d.title for d in safe])
        sparse = sorted(range(len(safe)), key=lambda i: scores[i], reverse=True)
        rrf = {i: 1 / (60 + rank) for rank, i in enumerate(sparse, 1) if scores[i] > 0}
        if self.models.s.mode == "local":
            try:
                if self.dense is None:
                    self.dense = self.models.embed([d.text for d in safe])
                vector = self.models.embed([query[:2000]], query=True)[0]
                similarities = self.dense @ vector
                order = sorted(range(len(safe)), key=lambda i: float(similarities[i]), reverse=True)
                for rank, i in enumerate(order, 1):
                    if float(similarities[i]) >= 0.72:
                        rrf[i] = rrf.get(i, 0) + 1 / (60 + rank)
                checks.append(
                    Check(
                        component="Hybrid retrieval",
                        status="complete",
                        detail="BM25 + multilingual E5, reciprocal-rank fusion. Similarity cutoff is experimental.",
                    )
                )
            except Exception:
                checks.append(
                    Check(
                        component="Dense retrieval",
                        status="unavailable",
                        detail="Embedding model unavailable; using BM25 only.",
                    )
                )
        else:
            checks.append(
                Check(component="Dense retrieval", status="skipped", detail="Baseline mode: BM25 only.")
            )
        candidates = sorted(rrf, key=rrf.get, reverse=True)[:15]
        if self.models.s.mode == "local" and candidates:
            try:
                ranked = self.models.rerank(query, [safe[i].text for i in candidates])
                candidates = [i for _, i in sorted(zip(ranked, candidates), reverse=True)]
                checks.append(
                    Check(
                        component="Reranking",
                        status="complete",
                        detail="Local multilingual cross-encoder reordered candidates.",
                    )
                )
            except Exception:
                checks.append(
                    Check(
                        component="Reranking",
                        status="unavailable",
                        detail="Cross-encoder unavailable; fused ranking retained.",
                    )
                )
        references = [safe[i].model_copy(update={"score": round(rrf[i], 5)}) for i in candidates[:3]]
        checks.append(
            Check(
                component="Evidence sufficiency",
                status="partial",
                detail="References explain general patterns; they do not verify sender identity, transactions or the submitted URL. Live web search is not enabled.",
            )
        )
        return references, checks
