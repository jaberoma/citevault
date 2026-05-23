"""ResumeParser tests using a small canned master résumé."""

from citevault.domain.models import Job, Project, Skill
from citevault.domain.services.resume_parser import parse_master_resume

SAMPLE = """\
# Experience

## Senior Backend Engineer · TechCorp · 2021-01 – present
- Led migration of payment service to Kubernetes.
- Mentored 2 junior engineers.

## Backend Engineer · StartupCo · 2018-06 – 2020-12
- Built REST APIs in Node.js.

# Projects

## KuberDocs — open-source K8s doc tool
- Written in Go, deployed via Helm.

# Skills
Java, Python, Kubernetes, Go
"""


def test_parser_extracts_jobs() -> None:
    result = parse_master_resume(SAMPLE, source_id="src-1")
    jobs = [e for e in result if isinstance(e, Job)]
    assert len(jobs) == 2
    assert jobs[0].company == "TechCorp"
    assert jobs[0].role == "Senior Backend Engineer"
    assert jobs[0].end_date is None
    assert "Led migration" in jobs[0].bullets[0]
    assert jobs[1].company == "StartupCo"
    assert jobs[1].end_date == "2020-12"


def test_parser_extracts_projects() -> None:
    result = parse_master_resume(SAMPLE, source_id="src-1")
    projects = [e for e in result if isinstance(e, Project)]
    assert len(projects) == 1
    assert projects[0].name == "KuberDocs"


def test_parser_extracts_skills() -> None:
    result = parse_master_resume(SAMPLE, source_id="src-1")
    skills = [e for e in result if isinstance(e, Skill)]
    skill_names = {s.name for s in skills}
    assert {"Java", "Python", "Kubernetes", "Go"} <= skill_names


def test_indented_bullets_are_extracted_correctly() -> None:
    text = "# Experience\n\n## Dev · Co · 2020-01 – present\n  - Did stuff.\n"
    result = parse_master_resume(text, source_id="s")
    jobs = [e for e in result if isinstance(e, Job)]
    assert jobs[0].bullets == ["Did stuff."]


def test_job_header_without_date_uses_sentinel() -> None:
    text = "# Experience\n\n## Engineer · Corp\n- Made things.\n"
    result = parse_master_resume(text, source_id="s")
    jobs = [e for e in result if isinstance(e, Job)]
    assert len(jobs) == 1
    assert jobs[0].start_date == "0000-00"
    assert jobs[0].end_date is None


def test_project_header_without_dash_uses_full_name() -> None:
    text = "# Projects\n\n## MyTool\n- Some detail.\n"
    result = parse_master_resume(text, source_id="s")
    projects = [e for e in result if isinstance(e, Project)]
    assert projects[0].name == "MyTool"


def test_bullet_formatted_skills_are_parsed() -> None:
    text = "# Skills\n- Python\n- Go\n"
    result = parse_master_resume(text, source_id="s")
    skills = [e for e in result if isinstance(e, Skill)]
    skill_names = {s.name for s in skills}
    assert {"Python", "Go"} <= skill_names


def test_empty_resume_returns_empty_list() -> None:
    assert parse_master_resume("", source_id="s") == []


def test_resume_missing_experience_section() -> None:
    text = "# Skills\nPython, Go\n"
    result = parse_master_resume(text, source_id="s")
    jobs = [e for e in result if isinstance(e, Job)]
    assert jobs == []
