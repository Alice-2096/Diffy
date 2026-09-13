from diffy.analyzers.diff import DiffAnalyzer


def test_detects_added_public_ingress() -> None:
    patch = """diff --git a/network.tf b/network.tf
--- a/network.tf
+++ b/network.tf
@@ -1,0 +2,1 @@
+  cidr_blocks = [\"0.0.0.0/0\"]
"""

    findings = DiffAnalyzer().analyze(patch)

    assert len(findings) == 1
    assert findings[0].category == "public_ingress"
    assert findings[0].file == "network.tf"


def test_ignores_removed_risky_line() -> None:
    patch = """diff --git a/network.tf b/network.tf
--- a/network.tf
+++ b/network.tf
@@ -2,1 +2,0 @@
-  cidr_blocks = [\"0.0.0.0/0\"]
"""

    assert DiffAnalyzer().analyze(patch) == []


def test_detects_wildcard_iam_action() -> None:
    patch = """diff --git a/iam.tf b/iam.tf
--- a/iam.tf
+++ b/iam.tf
@@ -1,0 +2,1 @@
+  actions = [\"s3:*\"]
"""

    findings = DiffAnalyzer().analyze(patch)

    assert [finding.category for finding in findings] == ["wildcard_iam"]
