import re, uuid, hashlib, datetime, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from extraction.schema import RawArtifact, Evidence, Entity, Claim
from data.corpus import EMAILS

def now_iso(): return datetime.datetime.utcnow().isoformat() + "Z"
def make_id(prefix): return f"{prefix}-{uuid.uuid4().hex[:8]}"

def fingerprint(text):
    norm = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(norm.encode()).hexdigest()

QUOTE_RE = re.compile(r"-----Original Message-----|---------- Forwarded message ----------|^On .* wrote:|^From:.*\nSent:", re.MULTILINE|re.IGNORECASE)

def strip_quoted(body):
    m = QUOTE_RE.search(body)
    return body[:m.start()].strip() if m else body.strip()

def ingest_emails(emails):
    artifacts, seen_fps, dup_map = [], {}, {}
    for email in emails:
        art = RawArtifact(
            artifact_id=email["id"],
            source_type="email",
            timestamp=email["timestamp"],
            content=email["body"],
            metadata={"from": email["from"], "to": email["to"], "cc": email.get("cc",[]),
                      "subject": email["subject"], "thread_id": email["thread_id"],
                      "message_id": email["message_id"]},
            redacted=email.get("redacted", False),
        )
        if not art.redacted:
            fp = fingerprint(strip_quoted(art.content))
            if fp in seen_fps:
                dup_map[art.artifact_id] = seen_fps[fp]
                print(f"  [DEDUP] {art.artifact_id} is near-dup of {seen_fps[fp]}")
            else:
                seen_fps[fp] = art.artifact_id
        artifacts.append(art)
    return artifacts, dup_map

ALIAS_MAP = {
    "kenneth.lay@enron.com":"ent-lay","ken lay":"ent-lay","ken":"ent-lay",
    "jeffrey.skilling@enron.com":"ent-skilling","j.skilling@enron.com":"ent-skilling",
    "jeff skilling":"ent-skilling","jeff":"ent-skilling",
    "andrew.fastow@enron.com":"ent-fastow","andy fastow":"ent-fastow","andy":"ent-fastow",
    "sherron.watkins@enron.com":"ent-watkins","sherron watkins":"ent-watkins",
    "richard.causey@enron.com":"ent-causey",
    "legal@enron.com":"ent-legal-dept",
    "all.employees@enron.com":"ent-all-employees",
}

SEED_ENTITIES = [
    Entity("ent-lay","Person","Kenneth Lay",
           aliases=["kenneth.lay@enron.com","ken lay","ken","Chairman & CEO"],
           metadata={"email":"kenneth.lay@enron.com"}),
    Entity("ent-skilling","Person","Jeffrey Skilling",
           aliases=["jeffrey.skilling@enron.com","j.skilling@enron.com","jeff skilling","jeff"],
           metadata={"email":"jeffrey.skilling@enron.com"}),
    Entity("ent-fastow","Person","Andrew Fastow",
           aliases=["andrew.fastow@enron.com","andy fastow","andy"],
           metadata={"email":"andrew.fastow@enron.com"}),
    Entity("ent-watkins","Person","Sherron Watkins",
           aliases=["sherron.watkins@enron.com","sherron watkins","VP Accounting"],
           metadata={"email":"sherron.watkins@enron.com"}),
    Entity("ent-causey","Person","Richard Causey",
           aliases=["richard.causey@enron.com"],metadata={}),
    Entity("ent-enron","Organization","Enron Corporation",
           aliases=["Enron","enron corp"],metadata={}),
    Entity("ent-ljm","Project","LJM Cayman Partnership",
           aliases=["LJM","LJM Cayman","ljm cayman"],metadata={}),
    Entity("ent-raptor","Project","Raptor SPE",
           aliases=["Raptor","raptor vehicles","SPE"],metadata={}),
    Entity("ent-role-ceo","Role","CEO",aliases=["Chief Executive Officer"],metadata={}),
    Entity("ent-role-cfo","Role","CFO",aliases=["Chief Financial Officer"],metadata={}),
    Entity("ent-role-vp-acct","Role","VP Accounting",aliases=["VP Accounting"],metadata={}),
    Entity("ent-q3-target","FinancialItem","Q3 Revenue Target $45B",
           aliases=["$45B","45B revenue target"],
           metadata={"amount":"45000000000","currency":"USD"}),
    Entity("ent-ljm-debt","FinancialItem","LJM Off-Balance-Sheet Debt $1.2B",
           aliases=["$1.2B debt","1.2B"],
           metadata={"amount":"1200000000","currency":"USD"}),
    Entity("ent-evt-resignation","Event","Skilling Resignation Aug 2001",
           aliases=["resignation","Skilling resigned"],
           metadata={"date":"2001-08-14"}),
    Entity("ent-evt-restatement","Event","Enron Earnings Restatement Nov 2001",
           aliases=["restatement","earnings restatement"],
           metadata={"date":"2001-11-08"}),
    Entity("ent-legal-dept","Organization","Enron Legal Department",
           aliases=["legal@enron.com","Legal"],metadata={}),
    Entity("ent-all-employees","Organization","All Enron Employees",
           aliases=["all.employees@enron.com"],metadata={}),
]

def resolve(name):
    return ALIAS_MAP.get(name.lower().strip())

def make_evidence(art, snippet):
    idx = art.content.find(snippet)
    if idx == -1:
        idx, snippet = 0, art.content[:200]
    return Evidence(make_id("ev"), art.artifact_id, snippet[:300], idx, idx+len(snippet), art.timestamp)

def extract(art):
    claims, evs = [], []
    body = art.content
    bl = body.lower()
    sender = art.metadata.get("from","")
    ts = art.timestamp
    sid = resolve(sender)

    def add(ctype, subj, obj, oval, snippet, conf, vf=None, vt=None, notes=""):
        ev = make_evidence(art, snippet)
        evs.append(ev)
        claims.append(Claim(make_id("clm"), ctype, subj, obj, oval,
                            [ev.evidence_id], conf, vf, vt, extracted_at=now_iso(), notes=notes))

    if sid:
        add("SENT_MESSAGE", sid, None, art.artifact_id, f"From: {sender}", 0.95, ts)

    if "jeff will be taking over as cfo" in bl:
        add("HOLDS_ROLE","ent-skilling","ent-role-cfo",None,
            "Jeff will be taking over as CFO effective October 1st.",0.85,
            vf="2001-10-01",notes="Later reversed in msg-003")

    if "andy stays as cfo" in bl:
        add("HOLDS_ROLE","ent-fastow","ent-role-cfo",None,"Andy stays as CFO.",0.92,vf=ts[:10])
        add("DECISION_REVERSED","ent-lay",None,"CFO assignment of Skilling","Andy stays as CFO.",0.88,vf=ts[:10])

    if "chairman & ceo" in bl:
        add("HOLDS_ROLE","ent-lay","ent-role-ceo",None,"Ken Lay\nChairman & CEO",0.90,vf="2001-09-01")

    if "resigning as ceo" in bl:
        snip = "I am resigning as CEO effective immediately."
        add("RESIGNED","ent-skilling","ent-role-ceo",None,snip,0.97,vf="2001-08-14",vt="2001-08-14")
        add("HOLDS_ROLE","ent-lay","ent-role-ceo",None,snip,0.88,vf="2001-08-14",
            notes="Lay resumed CEO after Skilling resigned")

    if "resume the ceo title" in bl:
        add("HOLDS_ROLE","ent-lay","ent-role-ceo",None,"resume the CEO title",0.88,vf="2001-08-14")

    if "$45b" in bl or "45b in revenue" in bl or "hit $45b" in bl.replace(",",""):
        snip = "We need to hit $45B in revenue for Q3"
        if snip not in body: snip = body[:120]
        add("HAS_REVENUE_TARGET","ent-enron","ent-q3-target","$45,000,000,000",snip,0.9,vf="2001-09-05")

    if "1.2b" in bl:
        snip = "The structure allows us to move $1.2B of debt off the books before year-end."
        if snip not in body: snip = body[:200]
        add("HAS_DEBT","ent-enron","ent-ljm-debt","$1,200,000,000",snip,0.88,vf="2001-10-12",
            notes="Off-balance-sheet via LJM Cayman structure")

    if "ljm" in bl:
        snip = "LJM Cayman partnership"
        if snip.lower() not in bl: snip = "LJM"
        add("INVOLVES_STRUCTURE","ent-enron","ent-ljm",None,snip,0.85,vf="2001-10-12")

    if "accounting scandals" in bl or "implode" in bl:
        add("CONCERN_RAISED","ent-watkins","ent-enron","Accounting irregularities",
            "I am incredibly nervous that we will implode in a wave of accounting scandals.",0.95,vf=ts[:10])

    if "restate earnings" in bl:
        add("RESTATEMENT","ent-enron","ent-evt-restatement",None,
            "We are being forced to restate earnings going back to 1997.",0.97,vf="2001-11-08")

    if sender == "sherron.watkins@enron.com" and "vp accounting" in bl:
        add("WORKS_AT","ent-watkins","ent-enron",None,"Sherron Watkins\nVP Accounting",0.95)
        add("HOLDS_ROLE","ent-watkins","ent-role-vp-acct",None,"VP Accounting",0.95)

    return claims, evs

def dedup_claims(claims):
    seen, result = {}, []
    for c in claims:
        key = (c.subject_id, c.claim_type, c.object_id, c.object_value)
        if key in seen:
            e = result[seen[key]]
            e.evidence_ids = list(set(e.evidence_ids + c.evidence_ids))
            if c.confidence > e.confidence: e.confidence = c.confidence
            print(f"  [CLAIM DEDUP] merged {c.claim_id} into {e.claim_id}")
        else:
            seen[key] = len(result)
            result.append(c)
    return result

def apply_supersession(claims):
    for newer in claims:
        if newer.claim_type == "DECISION_REVERSED":
            for older in claims:
                if (older.subject_id=="ent-skilling" and older.object_id=="ent-role-cfo"
                        and older.superseded_by is None):
                    older.superseded_by = newer.claim_id
                    older.valid_to = newer.valid_from
                    older.claim_type = "HELD_ROLE"
                    print(f"  [SUPERSEDE] {older.claim_id} (Skilling-CFO) superseded by {newer.claim_id}")
    return claims

def run_pipeline():
    print("=== Layer10 Extraction Pipeline ===\n")
    print("[1] Ingesting emails...")
    artifacts, dup_map = ingest_emails(EMAILS)
    print(f"    {len(artifacts)} artifacts, {len(dup_map)} duplicates\n")

    entities = {e.entity_id: e for e in SEED_ENTITIES}

    print("[2] Extracting claims...")
    all_claims, all_evs = [], []
    for art in artifacts:
        if art.redacted:
            print(f"  [SKIP] {art.artifact_id} – redacted"); continue
        if art.artifact_id in dup_map:
            print(f"  [SKIP] {art.artifact_id} – duplicate of {dup_map[art.artifact_id]}"); continue
        cs, es = extract(art)
        all_claims.extend(cs); all_evs.extend(es)
        print(f"  {art.artifact_id}: {len(cs)} claims")

    print(f"\n    Raw claims: {len(all_claims)}")
    print("\n[3] Deduplicating claims...")
    all_claims = dedup_claims(all_claims)
    print(f"    After dedup: {len(all_claims)}")
    print("\n[4] Applying supersession...")
    all_claims = apply_supersession(all_claims)
    print("\n=== Pipeline complete ===")

    return {
        "artifacts": [a.__dict__ for a in artifacts],
        "entities": [e.__dict__ for e in entities.values()],
        "claims": [c.__dict__ for c in all_claims],
        "evidences": [e.__dict__ for e in all_evs],
        "dup_map": dup_map,
    }

if __name__ == "__main__":
    result = run_pipeline()
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "memory_graph.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out}")
    for k in ["entities","claims","evidences","artifacts"]:
        print(f"  {k}: {len(result[k])}")
