"""Citevault CLI entry point."""

import os
import uuid
from pathlib import Path

import typer

from citevault import __version__
from citevault.adapters.outbound.markdown_renderer import render_gaps_markdown, render_resume_markdown
from citevault.adapters.outbound.pdf_renderer import markdown_to_pdf
from citevault.application.index_evidence import IndexEvidence
from citevault.application.run_evals import GoldenCaseRunner
from citevault.application.tailor_resume import TailorResume
from citevault.composition.container import Container, ContainerConfig
from citevault.domain.services.cover_letter import CoverLetterComposer
from citevault.domain.services.golden_loader import load_golden_case
from citevault.domain.services.job_posting_parser import JobPostingParser

app = typer.Typer(help="Citevault — local-first grounded résumé tailoring.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"citevault {__version__}")
        raise typer.Exit()


def _container() -> Container:
    return Container(ContainerConfig(
        db_path=os.environ.get("CITEVAULT_DB", "./citevault.db"),
        ollama_base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.environ.get("CITEVAULT_MODEL", "gemma4:e4b"),
        ollama_timeout_s=float(os.environ.get("CITEVAULT_LLM_TIMEOUT", "600")),
    ))


@app.command()
def index(folder: Path = typer.Argument(..., help="Evidence folder to index.")) -> None:
    """Index evidence from a folder into the local Citevault DB."""
    c = _container()
    c.wait_ready()
    use_case = IndexEvidence(repo=c.evidence_repo, embedder=c.embedder)
    report = use_case.run(str(folder))
    typer.echo(
        f"Indexed {report.sources_indexed} sources, "
        f"{report.spans_indexed} spans, "
        f"{report.structured_entries_indexed} structured entries."
    )


@app.command()
def tailor(
    job_file: Path = typer.Argument(..., help="Text file with the job posting."),
    output: Path = typer.Option(
        Path("./out"), "--output", "-o", help="Output folder."),
) -> None:
    """Tailor a résumé + cover letter against an indexed evidence base."""
    c = _container()
    c.wait_ready()
    try:
        posting_text = job_file.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError) as exc:
        typer.echo(f"Error: cannot read job file: {exc}", err=True)
        raise typer.Exit(1)
    parser = JobPostingParser(llm=c.llm)
    posting = parser.parse(posting_text=posting_text)

    use_case = TailorResume(
        retrieval=c.retrieval, reranker=c.reranker, llm=c.llm,
        span_lookup=c.evidence_repo, trace_repo=c.trace_repo,
    )
    tailoring_id = f"t-{uuid.uuid4().hex[:8]}"
    result = use_case.run(posting, tailoring_id=tailoring_id)

    span_texts: dict[str, str] = {}
    for claim in result.verified_claims:
        for cit in claim.citations:
            if cit.span_id and cit.span_id not in span_texts:
                sp = c.evidence_repo.get_span(cit.span_id)
                if sp:
                    span_texts[cit.span_id] = sp.text

    cover = CoverLetterComposer(llm=c.llm).compose(posting, result.verified_claims)

    output.mkdir(parents=True, exist_ok=True)
    resume_md = render_resume_markdown(result, span_texts)
    (output / "resume.md").write_text(resume_md)
    (output / "cover_letter.md").write_text(cover)
    (output / "gaps.md").write_text(render_gaps_markdown(result))
    markdown_to_pdf(resume_md, str(output / "resume.pdf"))

    typer.echo(
        f"Tailoring {tailoring_id}: "
        f"{len(result.verified_claims)} verified claims, "
        f"{len(result.gap_report.entries)} gaps. Output in {output}/."
    )


@app.command(name="eval")
def eval_(
    golden: Path = typer.Option(
        Path("./golden"), "--golden", "-g", help="Golden-set root directory."),
) -> None:
    """Run the golden regression suite. Exits non-zero on any case failure."""
    c = _container()
    c.wait_ready()
    cases = []
    for case_dir in sorted(p for p in golden.iterdir() if p.is_dir()):
        try:
            cases.append(load_golden_case(str(case_dir)))
        except FileNotFoundError:
            typer.echo(f"skip {case_dir.name}: incomplete case", err=True)
    if not cases:
        typer.echo("No golden cases found.", err=True)
        raise typer.Exit(code=2)

    runner = GoldenCaseRunner(
        embedder=c.embedder, reranker=c.reranker, llm=c.llm,
        db_path=os.environ.get("CITEVAULT_DB", "./citevault.db"),
    )
    result = runner.run_all(cases)

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo(f"Citevault golden-set evaluation — {result.started_at}")
    typer.echo("=" * 60)
    for ce in result.case_evaluations:
        flag = "PASS" if ce.case_passed else "FAIL"
        typer.echo(
            f"[{flag}] {ce.case_id:40s}  "
            f"First-Pass Grounding {ce.metrics.first_pass_grounding_rate:.0%}"
        )
        for v in ce.requirement_verdicts:
            sub = "v" if v.passed else "x"
            typer.echo(
                f"   {sub} {v.expectation.text:50s}  "
                f"expected={v.expectation.expected.value} actual={v.actual.value}"
            )
    typer.echo("-" * 60)
    typer.echo(
        f"Aggregate First-Pass Grounding Rate: {result.aggregate_first_pass:.1%}"
    )
    typer.echo(f"Overall: {'PASS' if result.overall_passed else 'FAIL'}")
    raise typer.Exit(code=0 if result.overall_passed else 1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
) -> None:
    """Start the FastAPI HTTP server."""
    import logging
    import uvicorn
    from citevault.adapters.inbound.http.app import create_app
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s %(name)s — %(message)s",
    )
    uvicorn.run(create_app(), host=host, port=port)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Citevault CLI."""
