# Task C: Triage of Semgrep Findings

Command in CI: `semgrep scan --config p/owasp-top-ten --error` (GitHub Actions, container `semgrep/semgrep`).

| Run | Date | Result | Evidence |
|---|---|---|---|
| Run 2 (before fixes) | 19 Nov 2026 | 176 rules, 7 files, **47 findings**, exit code 1 (red) | `task-c-01` to `task-c-03`, `task-c-run2-full-logs-47-findings.zip` |
| Run 3 (after fixes, on `main`) | 26 Nov 2026 | 177 rules, 11 files, **0 findings** (green) | `task-c-04`, `task-c-05`, `task-c-run3-full-logs-0-findings.zip` |

## Triage table (47 findings in run 2)

| # | Rule | `app.py` lines (before fixes) | Findings | Category | Reason | Fix (commit) |
|---|---|---|---|---|---|---|
| 1 | SQL injection: `tainted-sql-string` (Flask) | 21, 98, 140, 192, 221, 233, 270, 283, 328, 352, 362, 429 | 12 | **TP** | Form fields and the `username` cookie go into the SQL text with f-strings. An attacker can change them | `?` placeholders (`c122a43`) |
| 2 | Same rule, on `product_id` | 291, 336, 370, 373 | 4 | **FP** | Flask's `<int:product_id>` only lets whole numbers through. A number cannot carry SQL | `# nosemgrep` with the rule ID and this reason (`74b6a96`) |
| 3 | SQL injection: `sql-injection-db-cursor-execute` (Django rule) | 15 to 423 (same queries as row 1) | 20 | **DUP** | A Django rule on a Flask app. It reports the 12 queries of row 1 again, some more than once | Gone after `c122a43` |
| 4 | XSS: `directly-returned-format-string` (4) and `raw-html-format` (5) | 70, 318, 419, 462 and 299, 391, 405, 440 | 9 (4 TP + 5 DUP) | **TP** / **DUP** | Four pages (home, edit, product, admin) return HTML built with f-strings. The 4 return lines are the real flaw. The 5 `raw-html-format` reports are the same pages found by a second rule | Jinja2 templates (`fdb0f14`) |
| 5 | `debug-enabled` | 465 | 1 | **TP** | `app.run(debug=True)` opens the Flask debugger. It can run code | Debug only if `FLASK_DEBUG=1` (`27367db`) |
| 6 | `github-actions-mutable-action-tag` | workflow line 17 | 1 | **TP** | The tag `@v4` can be moved to different code (supply chain risk) | Pin to a commit SHA (`683bb38`) |

Total: 12 + 4 + 20 + 9 + 1 + 1 = **47**.

## Categories

| Category | Meaning | What I did |
|---|---|---|
| **TP** (true positive) | A real flaw | Fixed the code |
| **FP** (false positive) | The rule matches, but the flaw cannot happen | Suppressed with `# nosemgrep`, the rule ID and a reason |
| **DUP** (duplicate) | Another rule reports the same flaw | No separate action. It goes away with the fix |

The categories are my draft. I check every row myself before I use it in the report.

## Notes

- The CI log shows fewer blocks than 47, because Semgrep joins some findings into one block. I counted again by running the same community rules on the same original files. The total is 47, the same as the CI summary.
- Run 3 ran one more rule than run 2 (177 and 176). I did not check why, or which rule.
- The 4 suppressed lines (row 2) are safe only because of the `<int:>` route converter. Using `?` placeholders there too would be the better long-term fix. I kept the suppression to show triage.
- Fix commits are on branch `fix/semgrep-findings`, merged by pull request #1.
