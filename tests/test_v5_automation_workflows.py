from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MONITOR_WORKFLOW = ROOT / ".github" / "workflows" / "v5-ruleset-monitor.yml"
APPLY_WORKFLOW = ROOT / ".github" / "workflows" / "v5-apply-approved-update.yml"
VALIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "v5-validation.yml"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


class V5AutomationWorkflowTests(unittest.TestCase):
    def test_workflows_use_current_node24_action_majors(self) -> None:
        workflow_texts = [
            path.read_text(encoding="utf-8")
            for path in (MONITOR_WORKFLOW, APPLY_WORKFLOW, VALIDATE_WORKFLOW, PAGES_WORKFLOW)
        ]
        combined = "\n".join(workflow_texts)

        self.assertNotIn("actions/checkout@v4", combined)
        self.assertNotIn("actions/setup-python@v5", combined)
        self.assertNotIn("actions/github-script@v7", combined)
        self.assertNotIn("peter-evans/create-pull-request@v7", combined)
        self.assertIn("actions/checkout@v7", combined)
        self.assertIn("actions/setup-python@v6", combined)
        self.assertIn("actions/github-script@v9", combined)
        self.assertIn("peter-evans/create-pull-request@v8", combined)

    def test_daily_monitor_opens_issue_without_writing_repository(self) -> None:
        text = MONITOR_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("schedule:", text)
        self.assertIn("issues: write", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("manage-v5-rulesets.py monitor", text)
        self.assertNotIn("manage-v5-rulesets.py validate", text)

    def test_approval_workflow_requires_authorized_comment_and_only_creates_pr(self) -> None:
        text = APPLY_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("issue_comment:", text)
        self.assertIn("/approve-v5-ruleset-update", text)
        self.assertIn("OWNER", text)
        self.assertIn("MEMBER", text)
        self.assertIn("COLLABORATOR", text)
        self.assertIn("peter-evans/create-pull-request", text)
        self.assertIn("gh workflow run v5-validation.yml", text)
        self.assertNotIn("gh pr merge", text)
        self.assertNotIn("merge_method", text)

    def test_pull_requests_run_validation_before_manual_merge(self) -> None:
        text = VALIDATE_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("pull_request:", text)
        self.assertIn("python -m unittest discover", text)
        self.assertIn("manage-v5-rulesets.py validate", text)
        self.assertIn("build-v5-mvp-template.py --check", text)

    def test_pages_publishes_template_and_governed_snapshot_mirror(self) -> None:
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("rulesets/v5", text)
        self.assertIn("public/rulesets/v5/index.html", text)
        self.assertIn("manage-v5-rulesets.py validate", text)


if __name__ == "__main__":
    unittest.main()
