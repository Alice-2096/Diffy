from __future__ import annotations

import re

from diffy.review.findings import Finding, Severity


class DiffAnalyzer:
    """Small, explainable checks for added lines in a unified diff."""

    _rules = (
        (
            "public_ingress",
            Severity.HIGH,
            re.compile(r"(?:0\.0\.0\.0/0|::/0)"),
            "Public network range added",
            "Confirm that public ingress uses an approved edge or load balancer.",
        ),
        (
            "wildcard_iam",
            Severity.HIGH,
            re.compile(r'["\'](?:\*|[a-z0-9-]+:\*)["\']', re.IGNORECASE),
            "Wildcard IAM permission added",
            "Replace the wildcard with the smallest required action and resource set.",
        ),
        (
            "terraform_destroy",
            Severity.HIGH,
            re.compile(r"(?:will be destroyed|^-\s*resource\b)", re.IGNORECASE),
            "Terraform destroy signal found",
            "Review the affected resource and its blast radius before approval.",
        ),
        (
            "terraform_replace",
            Severity.MEDIUM,
            re.compile(r"must be replaced", re.IGNORECASE),
            "Terraform replacement signal found",
            "Confirm downtime, state movement, and replacement dependencies.",
        ),
    )

    def analyze(self, content: str) -> list[Finding]:
        findings: list[Finding] = []
        current_file: str | None = None

        for line_number, line in enumerate(content.splitlines(), start=1):
            if line.startswith("+++ b/"):
                current_file = line[6:]
                continue
            if not line.startswith("+") or line.startswith("+++"):
                continue

            added = line[1:]
            for category, severity, pattern, title, recommendation in self._rules:
                if pattern.search(added):
                    findings.append(
                        Finding(
                            category=category,
                            severity=severity,
                            title=title,
                            evidence=added.strip(),
                            recommendation=recommendation,
                            file=current_file,
                            diff_line=line_number,
                        )
                    )

        return findings
