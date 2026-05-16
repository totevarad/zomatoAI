# Edge cases and failure modes

This catalog lists **boundary conditions and failures** to handle when implementing the system described in [problemStatement.md](./problemStatement.md) and [architecture.md](./architecture.md). Use it for **test design**, **API error contracts**, and **orchestrator policies** (validation, filter, cap, LLM, merge, grounding).

**Conventions**

- **Hard constraints** (location, budget band, cuisine, minimum rating) belong in the **filter layer** so the candidate set stays valid (architecture §1, §4).
- **Soft preferences** (free-text `notes`: “quick lunch”, “family-friendly”) inform the **LLM prompt** only; they must not silently widen hard filters unless you explicitly choose that product behavior.

---

## 1. Data ingestion and canonical store

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| HF dataset **unavailable** (network, rate limit, auth) | No rows to recommend | Fail fast with clear error at ingest or startup; do not serve empty store as “no matches”. |
| **Schema drift** (columns renamed, types changed) | Mapping breaks silently | Version mapping; fail ingest on missing required columns; log diff. |
| **Missing** `name`, `location`, `cuisine`, `rating`, or cost field after mapping | Filter or display breaks | Drop row with metric; or quarantine with reason (document policy). |
| **Duplicate** logical restaurants (same name + location, different rows) | Double recommendations | Dedupe in ingest (keep best rating or merge) or stable `restaurant_id` + dedupe in results. |
| **No stable ID** in source | Merger cannot join LLM output | Derive `restaurant_id` from hash of canonical fields (architecture §5); document collision risk. |
| **Rating** null, non-numeric, or out of sensible range | Sorting and `min_rating` filter | Coerce or drop; never compare as string. |
| **Cost** missing or inconsistent with bands | Budget filter wrong | Map unknown to “unknown” and **exclude** from strict budget filter, or impute with documented rule. |
| **Location / cuisine** spelling variants (“Delhi” vs “New Delhi”, “Chinese” vs “chinese”) | Zero false negatives/positives | Normalize (trim, case); optional synonym table or fuzzy match with explicit UX (“did you mean …”). |
| **Multi-value cuisine** in one cell (“Chinese, Thai”) | Cuisine equality filter too strict | Match substring, tokenize, or “any of” policy; document. |
| **Very long** text fields in raw data | Token blow-up in LLM prompt | Truncate per field with ellipsis before prompt (architecture §7.3). |
| **Ingest on every request** vs stale file | Latency and consistency | Prefer load-once + optional refresh; document staleness. |

---

## 2. User input and API contract

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **Missing** required fields (`location`, `budget`, `cuisine`, `min_rating`) | Ambiguous query | `400` with field-level errors (architecture §8). |
| **`top_n`** missing, zero, negative, or very large | Abuse or accidental | Clamp to `[1, max]` (e.g. max 20); document default. |
| **`min_rating`** &gt; max rating in data or &gt; 5 | Always empty | Validate range; or return empty with message “no data in range”. |
| **`budget`** not in `{low, medium, high}` (or your enum) | Filter undefined | Reject or map with explicit default (prefer reject). |
| **Unknown `location` or `cuisine`** (not in allow-list / no fuzzy match) | User confusion vs empty set | Return `400` with suggestions, or `200` with empty + `meta.message` explaining unknown token (pick one product-wide). |
| **`notes` extremely long** | Token cost, prompt injection surface | Max length (chars); truncate server-side; never execute as code. |
| **`notes` with PII or instructions** (“ignore previous”, “return all restaurants”) | Safety and logging | Treat as **user preference text only** in system prompt; strip or no-log for observability (architecture §9). |
| **Unicode / emoji / RTL** in `notes` | Encoding and UI | UTF-8 end-to-end; UI escapes HTML if rendered as HTML. |
| **Concurrent identical requests** | Duplicate LLM cost | Optional idempotency key or short TTL cache on normalized request body. |

---

## 3. Filtering and candidate set

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **Zero** rows after filters | Valid user input, no venues | `200` with `results: []`, `meta.candidate_count: 0`, helpful message (architecture §6). |
| **Exactly one** row | LLM still invoked? | Allowed: short explanation; or skip LLM and return single row with templated line (document). |
| **Thousands** of rows match | Latency and LLM cost | **Cap** before LLM (e.g. 15–40) with deterministic **pre-sort** (architecture §4). |
| **Soft notes conflict** with hard filters (notes say “cheap”, budget already `low` but still no rows) | User expectation | Still return empty if hard filter yields zero; message should mention relaxing filters. |
| **Rating tie** on pre-sort | Unstable ordering | Secondary sort key (cost, name, `restaurant_id`) for reproducibility. |

---

## 4. LLM provider and adapter

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **Timeout** or **5xx** from provider | No ranking text | Fallback: deterministic top-K from capped list + `meta.warning` (architecture §7.3). |
| **429** rate limit | Same as outage | Backoff once; then fallback. |
| **Invalid API key** | Permanent failure until fixed | Clear `502`/config error at startup or first call; never silent empty. |
| **Response not JSON** / **schema mismatch** | Merger cannot run | Retry once with stricter instruction; then fallback (architecture §7.3). |
| **Partial JSON** (valid prefix only) | Parser fails | Same as invalid JSON. |
| **Empty** `ranked_ids` / `items` from model | No explanations to show | Fallback ordering + optional generic explanation line. |
| **Model returns fewer** than `top_n` IDs | UI expects N | Return available only; or pad from deterministic list without duplicate IDs. |

---

## 5. Grounding, merge, and display

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **`restaurant_id` in model output not in candidate batch** | Hallucination / copy error | **Drop** ID; optional retry with stricter system prompt (architecture §4, §7.3). |
| **Model invents **name** or numeric fields** instead of using IDs | Wrong facts shown | **Never** trust model for `name`, `rating`, `cost`; always **join from store** (architecture §7.2). |
| **Duplicate IDs** in ranked list | UI duplicates | Dedupe preserving first occurrence order. |
| **Explanation** references a **different** restaurant than the ID on the same row | Confusing UX | Hard to detect automatically; mitigate with prompt (“each explanation must match the id on the same object”). |
| **Explanation** in wrong language | Product expectation | Optional language param or system instruction; fallback to English. |

---

## 6. Presentation and UX

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **Slow** LLM (10–30s) | User abandons | Loading state; optional cancel; timeout aligned with adapter. |
| **API down** from browser | No results | Error banner; retry button. |
| **Empty results** | Looks like a bug | Dedicated empty state copy: “Try widening cuisine or lowering min rating.” |
| **Very long explanation** | Layout break | CSS clamp / “read more”; or server max length on explanation field. |
| **Screen readers** | Accessibility | Semantic list; announce result count. |

---

## 7. Operations, security, and compliance

| Edge case | Why it matters | Suggested behavior |
|-----------|----------------|---------------------|
| **Secrets** in client bundle | Key leak | Keys only on server / env (architecture §9, §10). |
| **Logging** full `notes` | PII in logs | Redact or hash; log length and flags only. |
| **Large file upload** if you add CSV later | DoS | Size limits; async processing. |

---

## 8. Traceability (quick map)

| Theme | Problem statement | Architecture |
|-------|-------------------|----------------|
| No invented venues | Success criteria §Problem (brief) | §1 grounding, §7, §4 MERGE |
| Soft vs hard prefs | Optional notes | §1 table, §4 FIL vs prompt |
| Empty / huge candidate sets | Decision fatigue / scale | §4 CAP, §6 alt branch |
| Provider failures | Reliability | §7.3, §9 |

---

## 9. Suggested test matrix (minimal)

1. **Ingest:** missing column → ingest fails loudly.  
2. **API:** invalid `budget` → `400`.  
3. **Filter:** impossible combination → `[]` + message.  
4. **Cap:** 500 matches → only first cap after pre-sort reaches LLM (assert via mock).  
5. **LLM mock:** returns unknown ID → dropped; remaining order valid.  
6. **LLM mock:** invalid JSON → fallback path returns deterministic list.  
7. **UI:** empty and error states render without crash.

For build order, see [implementation-plan.md](./implementation-plan.md).
