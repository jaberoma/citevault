"""GapReporter: structured gap entries for unmet requirements."""

from __future__ import annotations

from citevault.domain.models import GapEntry, GapReport, Requirement


class GapReporter:
    def report(
        self,
        tailoring_id: str,
        requirements: list[Requirement],
        met_requirement_ids: set[str],
        rejected_with_closest_evidence: dict[str, str],
    ) -> GapReport:
        entries: list[GapEntry] = []
        for req in requirements:
            if req.id in met_requirement_ids:
                continue
            closest = rejected_with_closest_evidence.get(req.id)
            if closest:
                suggestion = (
                    "Closest evidence found is too narrow. Consider whether to "
                    "expand it or flag this as a partial fit in the cover letter."
                )
            else:
                suggestion = (
                    "No supporting evidence in your sources. Consider: "
                    "(a) flagging as a learning interest in your cover letter, "
                    "(b) adding evidence if you have it elsewhere, "
                    "or (c) accepting that this role may not be the right fit."
                )
            entries.append(GapEntry(
                requirement_text=req.text, closest_evidence=closest,
                neutral_suggestion=suggestion,
            ))
        return GapReport(tailoring_id=tailoring_id, entries=entries)
