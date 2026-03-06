# Layer10 Take-Home — Grounded Long-Term Memory System

A pipeline that turns unstructured email communication into a **grounded memory graph** — where every extracted fact is traceable to its exact source sentence.

---

## Live Demo

Open `outputs/layer10_memory_graph.html` in any browser — no server needed.

- Click nodes to inspect entities and their claims
- Click edges to see evidence excerpts + full source emails
- Use the search bar to query the memory graph
- Quick-query buttons: CFO, Skilling, Watkins, Revenue, LJM

---

## Corpus

Synthetic Enron-style email dataset (`data/corpus.py`) — 10 emails covering:
- CFO role assignment and reversal (msg-001 → msg-003)
- LJM off-balance-sheet debt disclosure (msg-004, msg-008)
- Sherron Watkins whistleblower email (msg-005)
- Skilling resignation (msg-010)
- Earnings restatement + SEC investigation (msg-007)
- Redacted legal-hold message (msg-009)

To use the real Enron dataset instead:
```bash
# Download from Kaggle
kaggle datasets download wcukierski/enron-email-dataset
# Then replace EMAILS list in data/corpus.py with a loader for the CSV/mbox
```

---

## How to Run

No external packages required — Python 3.10+ stdlib only.

```bash
# 1. Run the extraction pipeline
python3 extraction/extractor.py
# → outputs/memory_graph.json  (17 entities, 21 claims, 30 evidences)

# 2. Run the retrieval demo
python3 retrieval/retriever.py
# → outputs/context_packs.json  (5 example Q&A results)

# 3. Open the visualization
open outputs/layer10_memory_graph.html
```

---

## Project Structure

```
layer10-takehome/
│
├── data/
│   └── corpus.py              # 10 synthetic Enron-style emails
│
├── extraction/
│   ├── schema.py              # Ontology: RawArtifact, Evidence, Entity, Claim
│   └── extractor.py           # Full pipeline: ingest → dedup → extract → supersede
│
├── retrieval/
│   └── retriever.py           # Keyword retrieval with scoring + context packs
│
├── outputs/
│   ├── memory_graph.json      # Serialized graph (run extractor.py to regenerate)
│   ├── context_packs.json     # 5 example Q&A results (run retriever.py to regenerate)
│   └── layer10_memory_graph.html  # Interactive visualization (open in browser)
│
└── README.md                  # This file (also serves as the full write-up)
```

---

## Architecture

```
Raw Emails
    │
    ▼
[1] INGEST + ARTIFACT DEDUP
    · SHA-256 fingerprint of stripped body detects forwarded/quoted duplicates
    · Redacted messages tombstoned — record kept, no claims extracted
    ▼
[2] STRUCTURED EXTRACTION
    · Rule-based patterns (deterministic, auditable)
    · Every claim gets an Evidence pointer: artifact_id + char offsets + excerpt
    · LLM pass (Claude claude-sonnet-4) stub shown in extractor.py comments
    ▼
[3] CLAIM DEDUPLICATION
    · Key: (subject_id, claim_type, object_id, object_value)
    · Evidence sets merged; highest confidence wins
    ▼
[4] SUPERSESSION
    · DECISION_REVERSED claims mark older HOLDS_ROLE as HELD_ROLE
    · valid_to set on superseded claims — history preserved, never deleted
    ▼
[5] MEMORY GRAPH  →  outputs/memory_graph.json
    ▼
[6] RETRIEVAL  →  outputs/context_packs.json
    · Entity-name + claim-type keyword scoring
    · Recency and confidence weighting
    · Superseded claims penalised but still returned (labelled HISTORICAL)
    ▼
[7] VISUALIZATION  →  outputs/layer10_memory_graph.html
```

---

## Ontology

### Entity Types
| Type | Description |
|------|-------------|
| Person | A human individual |
| Organization | A company, team, or department |
| Role | A job title (CEO, CFO, VP Accounting) |
| FinancialItem | Revenue target, debt amount, partnership |
| Project | A project or initiative (LJM Cayman, Raptor SPE) |
| Event | A discrete event (resignation, restatement) |

### Claim Types
| Claim | Meaning |
|-------|---------|
| HOLDS_ROLE | Person currently holds a Role |
| HELD_ROLE | Person historically held a Role (superseded) |
| WORKS_AT | Person works at Organization |
| RESIGNED | Person resigned from a Role |
| HAS_REVENUE_TARGET | Organization has a revenue target |
| HAS_DEBT | Organization has off-balance-sheet debt |
| INVOLVES_STRUCTURE | Entity involves a financial structure |
| DECISION_MADE | A decision was made |
| DECISION_REVERSED | A previously made decision was reversed |
| CONCERN_RAISED | A concern or whistleblower claim was raised |
| RESTATEMENT | Financial restatement announced |
| SENT_MESSAGE | Person sent a message (provenance) |

Every claim carries:
- `evidence_ids` → pointers to exact text spans in source emails
- `confidence` → 0.0–1.0 quality score
- `valid_from` / `valid_to` → bitemporal validity window
- `superseded_by` → claim_id that replaced this one (if reversed)
- `extraction_version` → for backfill tracking when ontology changes

---

## Deduplication

**Artifact level:** Strip quoted/forwarded content → SHA-256 fingerprint → skip if seen before.
- *Example:* msg-008 (forward of msg-004) correctly detected and skipped.

**Entity level:** `ALIAS_MAP` resolves `j.skilling@enron.com`, `jeff`, `Jeff Skilling` → single canonical entity `ent-skilling`.

**Claim level:** Merge on `(subject_id, claim_type, object_id, object_value)` — union evidence, keep max confidence.
- *Example:* "$45B revenue target" mentioned in msg-001, msg-002, msg-006 → 1 claim with 3 evidence pointers.

**Reversals:** Supersession marks old claims HELD_ROLE + sets valid_to. Nothing deleted. Fully reversible via audit log.

---

## Retrieval Results

| Question | Top Claim | Confidence | Evidence |
|----------|-----------|------------|---------|
| Who was CFO? | HOLDS_ROLE: Fastow → CFO | 92% | "Andy stays as CFO." (msg-003) |
| Did Skilling resign? | RESIGNED: Skilling → CEO | 97% | "I am resigning as CEO…" (msg-010) |
| What did Watkins raise? | CONCERN_RAISED → Enron | 95% | "implode in a wave of accounting scandals" (msg-005) |
| Q3 revenue target? | HAS_REVENUE_TARGET → $45B | 90% | 3 evidence sources (msg-001, 002, 006) |
| LJM debt? | HAS_DEBT → $1.2B | 88% | 3 evidence sources (msg-004, 007, 008) |

---

## Adapting to Layer10's Target Environment

### New entity types needed
- `Channel` — Slack channels as context containers
- `Ticket` — Jira/Linear tickets with structured state
- `Document` — Google Docs, Notion pages

### New claim types needed
- `DECISION_MADE` — formal decisions captured from chat/email
- `ACTION_ITEM` — tasks assigned in threads
- `STATE_TRANSITION` — ticket Open → InProgress → Done
- `MENTIONED_IN` — person/project referenced in a document

### Connecting chat to tickets
Extract `RELATED_TO` claims whenever a Jira ticket number appears in a Slack message or email body. This threads the discussion context directly to the structured work artifact.

### Durable memory vs ephemeral context
| Durable | Ephemeral |
|---------|-----------|
| Decisions with ≥2 evidence | Single mentions |
| Role assignments | Meeting small talk |
| Financial commitments | Draft messages |
| Escalations / concerns | Brainstorming threads |

Decay rule: claims with 1 evidence source and confidence < 0.6 age out after 90 days unless corroborated.

### Permissions
Every artifact carries an ACL. At query time, user's permission set is intersected with artifact ACLs — claims become invisible if all their evidence is inaccessible to that user.

### Grounding & safety
- Every LLM answer is constrained to claims present in the graph
- Each returned claim includes `artifact_id` + `char_start`/`char_end` for citation
- Redacted artifacts: wipe content, suspend dependent claims, restore if hold lifted
- No LLM output stored as memory without an evidence pointer

### Scaling
| Challenge | Solution |
|-----------|---------|
| Volume | Stream-process; no batch reprocessing needed |
| Cost | Rule-based first; LLM only for low-confidence patterns |
| Updates | Idempotent fingerprinting + claim dedup = safe re-runs |
| Evaluation | Hold-out labeled claim set; precision/recall per claim_type |
| Schema drift | `extraction_version` on every claim; backfill jobs for changes |
