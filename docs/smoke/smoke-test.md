# End-to-End Smoke Test (Web UI)

**Prerequisites:** Docker + Docker Compose. The stack is self-contained — no other smoke tests need to run first.

Validates: Docker stack boots, HTTP API responds, SSE stream works, React UI serves, Naive Comparison Mode works, evidence delete works.

Estimated time: ~5 minutes setup + ~2–10 minutes per tailoring (CPU-dependent).

---

## 1. Start the stack

```bash
cd /path/to/citevault

# Start Ollama first, then pull the model into the running server (one-time, ~1.5 GB)
docker compose up -d ollama
docker compose exec ollama ollama pull gemma4:e4b

# Start remaining services
docker compose up -d

# Confirm services are healthy
docker compose ps
curl -s http://localhost:8000/api/health
```

**Expected health response:**
```json
{"status": "ok", "local_models": "ready", "ollama": "ok", "model": "available"}
```

If the container is still warming up (BGE models loading) you may receive `{"status": "loading", "local_models": "loading", ...}` — wait a few seconds and retry. If Ollama is unreachable the status will be `"error"`.

---

## 2. Verify the React UI serves

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/admin
```

**Expected:** `200`

Open `http://localhost:5173/admin` in a browser. You should see the **Evidence Library** heading.

---

## 3. Evidence management (HTTP API)

### 3a. Upload evidence
```bash
# Create a test evidence file
cat > /tmp/test_evidence.md <<'EOF'
# Experience

## Senior Backend Engineer · TechCorp · 2021–present
- Led migration of payment service to Kubernetes (Helm-based deployment).
- Reduced API latency 40% via Redis caching layer redesign.
- Mentored 2 junior engineers through promotion cycle.

## Backend Engineer · StartupCo · 2018–2020
- Built REST APIs in Node.js serving 50 k DAU.

# Skills
Java, Quarkus, Kubernetes, Python, Redis, Node.js
EOF

curl -s -X POST http://localhost:8000/api/evidence/source \
  -F "file=@/tmp/test_evidence.md" | python3 -m json.tool
```

**Expected:** JSON with `id`, `kind`, `path`.

### 3b. List sources
```bash
curl -s http://localhost:8000/api/evidence | python3 -m json.tool
```

**Expected:** `{"sources": [{"id": "...", ...}]}` — one entry.

### 3c. Delete a source
```bash
SOURCE_ID=<id from 3a>
curl -s -X DELETE http://localhost:8000/api/evidence/source/$SOURCE_ID -w "%{http_code}"
curl -s http://localhost:8000/api/evidence | python3 -m json.tool
```

**Expected:** `204` from delete, then `{"sources": []}` from list.

Re-upload the evidence file before continuing (needed for step 4).

---

## 4. Tailoring — grounded mode

```bash
# Re-upload if deleted above
SOURCE_ID=$(curl -s -X POST http://localhost:8000/api/evidence/source \
  -F "file=@/tmp/test_evidence.md" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

JOB_POSTING='Senior Backend Engineer — Cloud Infrastructure

Required:
- 5+ years building distributed systems
- Kubernetes in production
- Mentorship experience valued

Bonus:
- Go or Rust experience'

# Start tailoring (returns HTTP 202 — job runs asynchronously)
TAILOR_ID=$(curl -s -X POST http://localhost:8000/api/tailor \
  -H 'Content-Type: application/json' \
  -d "{\"job_posting\": $(echo "$JOB_POSTING" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tailoring_id'])")

echo "Tailoring ID: $TAILOR_ID"
```

### 4a. Poll for completion
```bash
# Poll every 10 seconds (CPU inference is slow)
for i in $(seq 1 30); do
  STATUS=$(curl -s http://localhost:8000/api/tailor/$TAILOR_ID \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))")
  echo "[$i] Status: $STATUS"
  [ "$STATUS" = "complete" ] && break
  sleep 10
done
```

**Expected:** eventually `complete`.

### 4b. Inspect result
```bash
curl -s http://localhost:8000/api/tailor/$TAILOR_ID | python3 -m json.tool | head -60
```

**Verify:**
- `status` = `"complete"`
- `resume_md` contains text with `[^sp-...]` citation footnotes
- `cover_letter_md` contains text
- `verified_claims` is a list with at least one entry
- `gap_report` is a list (may be empty if all requirements grounded)
- `summary.first_pass_verified` ≥ 1
- `naive_md` is `null` (not requested)
- `pdf_ready` is `true` (generated in background; may take a few seconds after `complete`)

### 4c. Download PDF
```bash
curl -o /tmp/resume.pdf http://localhost:8000/api/tailor/$TAILOR_ID/pdf
file /tmp/resume.pdf
```

**Expected:** `PDF document` in the output.

---

## 5. SSE stream verification

```bash
# Start a new tailoring and watch the stream
TAILOR_ID2=$(curl -s -X POST http://localhost:8000/api/tailor \
  -H 'Content-Type: application/json' \
  -d "{\"job_posting\": $(echo "$JOB_POSTING" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tailoring_id'])")

curl -sN http://localhost:8000/api/tailor/$TAILOR_ID2/stream
```

**Expected:** a stream of SSE events:
```
data: {"event": "started", "data": {"tailoring_id": "t-..."}}

data: {"event": "posting_parsed", "data": {"requirements_count": N}}

data: {"event": "requirement_started", "data": {"req_id": "...", "text": "..."}}

data: {"event": "retrieval_done", "data": {"req_id": "...", "candidate_count": N}}

data: {"event": "claim_finalized", "data": {"claim_id": "...", "status": "VERIFIED|REWRITTEN|REJECTED", "text": "...", "verdict": "..."}}

data: {"event": "complete", "data": {"tailoring_id": "t-..."}}
```

Hit Ctrl+C once you see `"event": "complete"`.

---

## 6. Naive Comparison Mode

```bash
TAILOR_ID3=$(curl -s -X POST http://localhost:8000/api/tailor \
  -H 'Content-Type: application/json' \
  -d "{\"job_posting\": $(echo "$JOB_POSTING" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'), \"naive_compare\": true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tailoring_id'])")

# Poll...
for i in $(seq 1 40); do
  STATUS=$(curl -s http://localhost:8000/api/tailor/$TAILOR_ID3 \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))")
  [ "$STATUS" = "complete" ] && break
  echo "[$i] waiting..."; sleep 10
done

curl -s http://localhost:8000/api/tailor/$TAILOR_ID3 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('naive_md present:', bool(d.get('naive_md')))"
```

**Expected:** `naive_md present: True`

---

## 7. Settings API

```bash
curl -s http://localhost:8000/api/settings | python3 -m json.tool
```

**Expected:** JSON with `model` and `available` fields:
```json
{"model": "gemma4:e4b", "available": true}
```

---

## 8. Newman (automated API tests)

Sections 3 and 7 above can be run automatically using the Postman collection at `docs/smoke/citevault.postman_collection.json`.

**Prerequisites:**
```bash
npm install -g newman   # or use npx
```

The collection uploads `docs/smoke/fixtures/test_evidence.md` in step 02. Run from the repo root (as shown below) so `--working-dir .` resolves the fixture path correctly.

**Run (from repo root):**
```bash
npx newman run docs/smoke/citevault.postman_collection.json \
  --working-dir . \
  --delay-request 500 \
  --timeout 30000
```

**What it covers (9 requests):**

| # | Request | Assertions |
|---|---------|-----------|
| 01 | Health Check | `status: "ok"`, `ollama: "ok"`, `model: "available"` |
| 02 | Upload Evidence | returns `id` + `kind` |
| 03 | List Evidence | uploaded source present |
| 04 | Get Settings | `model` field present |
| 05 | Update Settings | PUT accepted; `model` returned |
| 06 | Verify Settings Persisted | `model` persists across requests |
| 07 | Confirm Settings Idempotent | second PUT with same value accepted |
| 08 | Delete Evidence | 204 |
| 09 | Verify Evidence Deleted | source gone from list |

**Not automated:** SSE stream (Newman has no SSE support), tailoring/PDF (LLM inference too slow for automated runs), and Naive Comparison Mode. Run those manually via sections 4–6 above.

---

## 9. Playwright smoke tests (headless)

```bash
cd /path/to/citevault/citevault-ui
npm install
npx playwright install chromium
npx playwright test --reporter=line
```

**Expected:** 4 tests pass:
```
✓ Admin page loads and shows Evidence Library heading
✓ Settings page loads and shows model field
✓ New Tailoring page loads with job posting textarea
✓ History page loads
```

Requires the docker compose stack from step 1 to still be running.

---

## 10. Teardown

```bash
cd /path/to/citevault
docker compose down
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `curl: Connection refused :8000` | citevault-api not started | `docker compose up -d citevault-api` |
| Upload returns 500 | BGE model download on first call (slow) | Wait 30s and retry |
| Tailoring stuck `running` | Ollama slow on CPU | Allow up to 5 min per request |
| SSE stream closes immediately | nginx proxy buffering | Check `nginx.conf` has `proxy_buffering off` |
| `naive_md` is null with `naive_compare: true` | LLM call failed | Check `docker compose logs citevault-api` |
| Playwright tests fail | Stack not running | Ensure step 1 is complete |
