"""
retriever.py – Simple retrieval over the memory graph.

Given a question, we:
1. Keyword-match against entity canonical_name + aliases
2. Keyword-match against claim_type labels + object_value
3. Expand to neighbouring claims for each matched entity
4. Score by (confidence * recency_boost * evidence_count)
5. Return a ranked context pack with evidence excerpts

In production you would replace keyword lookup with embedding similarity
(e.g. sentence-transformers + pgvector) for semantic retrieval.
"""

import json, re, os, sys
from datetime import datetime

GRAPH_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "memory_graph.json")

def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)

def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def recency_score(ts):
    if not ts: return 0.5
    try:
        d = datetime.fromisoformat(ts.replace("Z",""))
        baseline = datetime(2001, 1, 1)
        days = (d - baseline).days
        return min(1.0, days / 365)
    except:
        return 0.5

def retrieve(question: str, top_k: int = 5) -> dict:
    g = load_graph()
    entities = {e["entity_id"]: e for e in g["entities"]}
    evidences = {e["evidence_id"]: e for e in g["evidences"]}
    artifacts = {a["artifact_id"]: a for a in g["artifacts"]}
    claims = g["claims"]

    qtoks = tokenize(question)

    # Score entities by name/alias overlap
    entity_scores = {}
    for eid, ent in entities.items():
        names = [ent["canonical_name"]] + ent.get("aliases", [])
        all_toks = tokenize(" ".join(names))
        overlap = len(qtoks & all_toks)
        if overlap > 0:
            entity_scores[eid] = overlap

    # Score claims by entity match + claim_type keyword match
    CLAIM_KEYWORDS = {
        "HOLDS_ROLE": {"role","title","cfo","ceo","vp","holds","position"},
        "HELD_ROLE": {"was","former","previously","held","historical"},
        "RESIGNED": {"resign","quit","left","departure"},
        "HAS_REVENUE_TARGET": {"revenue","target","billion","money","earnings"},
        "HAS_DEBT": {"debt","balance","sheet","liability","off-balance"},
        "CONCERN_RAISED": {"concern","worry","whistleblow","accounting","scandal"},
        "RESTATEMENT": {"restate","restatement","sec","investigation"},
        "DECISION_REVERSED": {"reversed","changed","overturned","correction"},
        "INVOLVES_STRUCTURE": {"ljm","partnership","spe","structure","raptor"},
        "SENT_MESSAGE": {"sent","email","wrote","message"},
        "WORKS_AT": {"works","employed","staff","employee"},
    }

    scored = []
    for c in claims:
        score = 0.0
        reasons = []

        # Entity match
        if c["subject_id"] in entity_scores:
            score += entity_scores[c["subject_id"]] * 0.4
            reasons.append(f"subject matches query")
        if c["object_id"] and c["object_id"] in entity_scores:
            score += entity_scores[c["object_id"]] * 0.3
            reasons.append(f"object matches query")

        # Claim type keyword match
        ck = CLAIM_KEYWORDS.get(c["claim_type"], set())
        if qtoks & ck:
            score += 0.3
            reasons.append(f"claim type '{c['claim_type']}' matches")

        # Object value text match
        if c.get("object_value"):
            ov_toks = tokenize(c["object_value"])
            if qtoks & ov_toks:
                score += 0.2
                reasons.append("object value matches")

        if score == 0:
            continue

        # Confidence boost
        score *= c["confidence"]

        # Recency boost (use valid_from or first evidence timestamp)
        ev_ts = ""
        if c["evidence_ids"]:
            first_ev = evidences.get(c["evidence_ids"][0])
            if first_ev:
                ev_ts = first_ev.get("timestamp", "")
        score *= (0.7 + 0.3 * recency_score(c.get("valid_from") or ev_ts))

        # Penalise superseded claims slightly
        if c.get("superseded_by"):
            score *= 0.5
            reasons.append("(historical – superseded)")

        scored.append((score, c, reasons))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]

    # Build context pack
    result_claims = []
    for score, c, reasons in top:
        ev_snippets = []
        for eid in c["evidence_ids"]:
            ev = evidences.get(eid)
            if not ev: continue
            art = artifacts.get(ev["artifact_id"], {})
            ev_snippets.append({
                "evidence_id": eid,
                "artifact_id": ev["artifact_id"],
                "excerpt": ev["excerpt"],
                "timestamp": ev["timestamp"],
                "source_metadata": art.get("metadata", {}),
            })

        subj_name = entities.get(c["subject_id"],{}).get("canonical_name", c["subject_id"])
        obj_name = (entities.get(c["object_id"],{}).get("canonical_name", c["object_id"])
                    if c["object_id"] else c.get("object_value",""))

        result_claims.append({
            "claim_id": c["claim_id"],
            "claim_type": c["claim_type"],
            "subject": subj_name,
            "object": obj_name,
            "confidence": c["confidence"],
            "valid_from": c.get("valid_from"),
            "valid_to": c.get("valid_to"),
            "superseded_by": c.get("superseded_by"),
            "score": round(score, 3),
            "reasons": reasons,
            "evidence": ev_snippets,
        })

    return {
        "question": question,
        "matched_entities": [entities[eid]["canonical_name"] for eid in entity_scores],
        "results": result_claims,
    }

SAMPLE_QUESTIONS = [
    "Who was CFO of Enron?",
    "Did Skilling resign?",
    "What concerns did Sherron Watkins raise?",
    "What was the Q3 revenue target?",
    "What happened with the LJM debt?",
]

if __name__ == "__main__":
    import json
    out_packs = []
    for q in SAMPLE_QUESTIONS:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        pack = retrieve(q)
        out_packs.append(pack)
        for r in pack["results"][:3]:
            sup = " [HISTORICAL]" if r["superseded_by"] else ""
            print(f"  [{r['score']:.2f}] {r['claim_type']}: {r['subject']} → {r['object']}{sup}")
            if r["evidence"]:
                print(f"    Evidence: \"{r['evidence'][0]['excerpt'][:80]}...\"")

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "context_packs.json")
    with open(out_path, "w") as f:
        json.dump(out_packs, f, indent=2)
    print(f"\nContext packs saved to {out_path}")
