# Task C: Automated Security Testing (Semgrep in GitHub Actions)

This folder shows the evidence for Task C, in the order it happened.

## What happened

1. Run 1 passed (green) but did not scan. The old Semgrep action crashed and still reported success.
2. Run 2 failed (red). The current Semgrep found 47 findings. This is the first evidence.
3. I fixed the real flaws, suppressed 4 false positives with a reason, and pinned one action. Five commits, one pull request.
4. Run 3 passed (green) with 0 findings. This is the second evidence.

## Files

| File | What it shows |
|---|---|
| `task-c-00-run1-green-but-no-scan.png` | Run 1 is green |
| `task-c-00-run1-silent-failure-log.txt` | Run 1 log: Semgrep crashed with `invalid rule severity value: MEDIUM` |
| `task-c-00-run1-full-logs.zip` | Run 1 full log |
| `task-c-01-run2-red-build.png` | Run 2 is red (evidence 1) |
| `task-c-02-run2-sqli-login-line140.png` | One finding: SQL injection in the login route |
| `task-c-03-run2-scan-summary.png` | Run 2 summary: 47 findings |
| `task-c-run2-full-logs-47-findings.zip` | Run 2 full log |
| `task-c-04-run3-green-build.png` | Run 3 is green, after the merge into `main` (evidence 2) |
| `task-c-05-run3-scan-summary-0-findings.png` | Run 3 summary: 0 findings |
| `task-c-run3-full-logs-0-findings.zip` | Run 3 full log |
| `task-c-triage-table.md` | Each finding group: category, reason and the commit that fixed it |

## Workflow choice

The workflow uses the `semgrep/semgrep` container. The lab sheet uses `pip install semgrep`. Both give the same result: the current Semgrep, the same `p/owasp-top-ten` rules and the same `--error` flag. The container is faster because Semgrep is already installed.

## Known limits

- The Semgrep version and the rules are not pinned. A later version could give a different result. This is the same kind of problem that made the old action fail.
- `actions/checkout` is pinned to a commit SHA (v4.4.0). Run 3 shows it works in CI.
- Four findings are suppressed because `product_id` is a whole number from the route. A `?` placeholder would be safer.
