# Evidence format guide

Citevault grounds every résumé claim in the evidence you provide. The richer and
better-structured your evidence files, the better the output.

---

## Supported file types

| File | What it contributes |
|------|---------------------|
| `master_resume.md` (or `resume.md`) | Structured Experience + Projects + Skills, plus retrieval chunks |
| Any other `.md` / `.txt` | Retrieval chunks only (blog posts, project write-ups, notes) |
| `.pdf` | Retrieval chunks (text extracted via pypdf) |

Place all files in the `evidence/` folder before running `docker compose up -d`.

---

## Master résumé format

The master résumé is the only file parsed for structured data (Experience, Projects,
Skills). It must be a Markdown file whose **name contains `master_resume` or `resume`**
(case-insensitive).

### Required conventions

- Top-level sections use `#` headings: `# Experience`, `# Projects`, `# Skills`
- Experience entries use `##` headings: `## Role · Company · YYYY-MM – YYYY-MM`
  - Date separator can be `–` (en-dash) or `-`
  - Use `present` instead of an end date for your current role
  - Month is required: `2021-01`, not `2021`
- Project entries use `##` headings: `## Project Name — optional subtitle`
- Skills are a comma- or newline-separated list under `# Skills`
- Bullets use `- ` (dash + space)

### Example

```markdown
# Experience

## Senior Backend Engineer · Acme Corp · 2022-03 – present
- Designed and led migration of monolithic billing service to event-driven
  architecture using Kafka, processing 3M events/day.
- Reduced P99 API latency from 800 ms to 120 ms via Redis caching redesign.
- Mentored 3 junior engineers; 2 promoted within 18 months.
- Owned on-call rotation for the payments domain (6 services).

## Backend Engineer · StartupCo · 2019-06 – 2022-02
- Built REST APIs in Go serving 80 k DAU; maintained 99.95% uptime SLA.
- Introduced contract testing (Pact) that cut integration bugs by 60%.
- Collaborated with data team to ship real-time fraud detection pipeline.

## Software Engineer · ConsultingFirm · 2017-09 – 2019-05
- Delivered 4 client projects in Java/Spring Boot across fintech and retail.

# Projects

## KuberDocs — internal Kubernetes runbook platform
- Built a GitOps-driven docs site serving 200+ engineers.
- Integrated with PagerDuty to surface runbooks during active incidents.

## Distributed Systems Book — internal engineering resource
- Authored 12-chapter internal book on distributed system patterns.
- Read by ~600 engineers across 3 offices; used in onboarding for 2 years.

# Skills
Go, Java, Python, Kubernetes, Helm, Terraform, Kafka, PostgreSQL, Redis,
gRPC, Docker, GitHub Actions, Prometheus, Grafana, AWS, GCP
```

---

## Supplementary evidence files

Any other `.md`, `.txt`, or `.pdf` file in `evidence/` is chunked and indexed for
retrieval. Good additions:

- **Blog posts** — detailed write-ups of technical decisions
- **Project READMEs** — scope, tech stack, your specific role
- **Performance review excerpts** — concrete achievements with numbers
- **Conference talk abstracts** — signals thought leadership

These files do **not** need to follow any special format. The more specific and
concrete the content, the better Citevault can ground claims against it.

---

## Tips

- **Numbers matter.** "Reduced latency 40%" is far more groundable than
  "improved performance". Include concrete metrics wherever possible.
- **One file per concern.** A blog post about caching and a project README about
  Kubernetes are better kept separate — it improves retrieval precision.
- **Re-index after changes.** If you edit an evidence file, delete and re-upload
  it via the Admin UI (or restart with a fresh database) so the new version is indexed.
