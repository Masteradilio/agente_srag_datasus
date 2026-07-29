# MASTER BACKLOG V2 — Agente SRAG DataSUS

## 1. Purpose

This backlog turns the current proof of concept into a technically credible,
reproducible, and publicly presentable open-source portfolio project.

The project must remain focused on its strongest proposition:

> An auditable AI agent that produces epidemiological reports from official
> Brazilian SRAG data while keeping metric computation deterministic and using
> the LLM only for controlled orchestration and analytical writing.

This is not a plan to turn the repository into a generic agent platform or a
commercial SaaS product. The work below prioritizes architectural truth,
grounded retrieval, safety evaluation, reproducibility, and evidence that a
technical reviewer can verify.

## 2. Execution Rules

- Complete phases in order unless a task explicitly says it can run in parallel.
- Keep deterministic epidemiological calculations outside the LLM.
- Every behavior-changing task must add or update targeted tests.
- Do not label a capability as implemented until its acceptance criteria pass.
- Keep generated data and run artifacts out of Git unless they are intentional,
  anonymized fixtures.
- Prefer small, reviewable pull requests. One task may become more than one pull
  request when the change is large.
- Record baseline and post-change evidence under `artifacts/benchmarks/`.
- Public documentation must distinguish calculated facts, retrieved evidence,
  LLM-generated interpretation, and methodological limitations.

## 3. Definition of Done

A task is done only when:

- its implementation and targeted tests are complete;
- `ruff check` and `mypy` pass for the changed modules;
- the relevant test module passes;
- public behavior or architecture changes are documented;
- no secret, downloaded health dataset, or personal data is committed;
- acceptance evidence is linked in the pull request or stored as a small,
  reproducible artifact.

## 4. Phase Overview

| Phase | Outcome | Exit gate |
|---|---|---|
| 0 | Truthful baseline and public positioning | Claims match the implementation and a reproducible baseline exists |
| 1 | Real LangGraph orchestration | The compiled graph is the production execution path |
| 2 | Measured, grounded retrieval | Retrieval quality and source provenance are evaluated |
| 3 | Safety and quality evaluation | Adversarial and epidemiological regression suites pass |
| 4 | Run observability and audit UX | A reviewer can inspect how a report was produced |
| 5 | Reproducible delivery | CI, container, and one-command demo work from a clean clone |
| 6 | Public portfolio release | Repository communicates value and evidence within minutes |
| 7 | Optional research extensions | Enhancements add evidence without obscuring the core project |

---

## Phase 0 — Baseline, Architectural Truth, and Positioning

### SRAG-V2-000 — Freeze a reproducible technical baseline

**Priority:** P0  
**Dependencies:** none

**Tasks**

- [ ] Record the Python version, dependency installation command, test command,
  lint command, type-check command, and Streamlit start command.
- [ ] Execute one fixture-based end-to-end run and record its duration, input row
  count, output artifacts, and final validation status.
- [ ] Execute one real-data run without committing the downloaded dataset.
- [ ] Store small baseline results in
  `artifacts/benchmarks/v2_baseline_summary.json`.
- [ ] Document expected network-dependent steps and deterministic offline
  fallbacks.

**Acceptance criteria**

- A clean clone can reproduce the fixture run using documented commands.
- The baseline JSON includes timestamp, Git commit, environment, test summary,
  run duration, report validation result, and artifact paths.
- “Baseline completed” and “quality target achieved” are reported separately.

### SRAG-V2-001 — Reposition the repository as a public-health engineering case study

**Priority:** P0  
**Dependencies:** SRAG-V2-000

**Tasks**

- [ ] Replace challenge-specific framing in the main README with a concise
  problem, audience, approach, and evidence section.
- [ ] Preserve the original hiring challenge only as historical context in a
  secondary document.
- [ ] Add a “What this project proves” section covering deterministic analytics,
  controlled tool use, grounded writing, guardrails, and auditability.
- [ ] Add an explicit “What this project does not claim” section covering
  diagnosis, individual medical advice, hospital-bed occupancy, population
  vaccine coverage, and real-time surveillance guarantees.
- [ ] Define a stable public name, one-sentence description, and repository
  topics for GitHub.

**Acceptance criteria**

- A reviewer can understand the use case, architectural differentiator, and
  limitations from the first screen of the README.
- No public claim implies that a proxy metric is a population or hospital
  occupancy metric.

### SRAG-V2-002 — Make architecture documentation match runtime reality

**Priority:** P0  
**Dependencies:** SRAG-V2-000

**Tasks**

- [ ] Document the current manual orchestration path before changing it.
- [ ] Describe the current retrieval implementation as lexical token-overlap
  search; do not call it a vector database.
- [ ] Add one component diagram and one report-generation sequence diagram.
- [ ] Mark planned LangGraph, hybrid retrieval, tracing, and evaluation
  capabilities as planned until their phase exit gates pass.
- [ ] Add an architecture decision record for keeping metric calculations
  deterministic and outside the LLM.

**Acceptance criteria**

- Every major box in the diagrams maps to an implemented module.
- Documentation clearly differentiates current, planned, and optional behavior.

### SRAG-V2-003 — Establish release governance

**Priority:** P1  
**Dependencies:** none

**Tasks**

- [ ] Add or verify an open-source license compatible with the intended public
  contribution.
- [ ] Add `CONTRIBUTING.md`, a security-reporting policy, and issue templates.
- [ ] Define semantic versioning and release criteria.
- [ ] Define a data policy covering downloaded DataSUS files, cached news,
  generated reports, fixtures, and retention.

**Acceptance criteria**

- Contributors know how to install, test, report vulnerabilities, and avoid
  committing sensitive or oversized data.

**Phase 0 exit gate**

- [ ] Baseline evidence is committed.
- [ ] Architecture and retrieval claims are truthful.
- [ ] Public scope and limitations are unambiguous.

---

## Phase 1 — Real LangGraph Runtime

### SRAG-V2-100 — Replace passthrough nodes with executable graph nodes

**Priority:** P0  
**Dependencies:** SRAG-V2-002

**Tasks**

- [ ] Convert each step in `AGENT_STEP_ORDER` into a node that executes its real
  behavior and returns an explicit state update.
- [ ] Inject tools and run-specific paths through a typed runtime context instead
  of hidden globals.
- [ ] Make `run_agent_graph()` invoke the compiled LangGraph workflow.
- [ ] Remove the duplicate manual sequence after graph parity is proven.
- [ ] Keep node names stable in audit traces.

**Targeted tests**

- [ ] Update `tests/test_agent_graph.py` to prove that compiled graph invocation
  produces the expected final state.
- [ ] Add a test that fails if the production entry point bypasses the compiled
  graph.
- [ ] Preserve tool injection tests using deterministic fakes.

**Acceptance criteria**

- There is one production orchestration path.
- A graph node failure is attributed to its node in `agent_trace.jsonl`.
- The fixture-based report remains equivalent in required sections and metrics.

### SRAG-V2-101 — Add typed routing and failure classification

**Priority:** P0  
**Dependencies:** SRAG-V2-100

**Tasks**

- [ ] Add state fields for node status, failure category, attempt count,
  warnings, and recoverability.
- [ ] Classify failures as validation, transient network/provider, data,
  security, or internal.
- [ ] Add conditional edges for retry, deterministic fallback, safe failure, and
  successful completion.
- [ ] Permit retries only for explicitly transient operations.
- [ ] Cap retries and record the terminal decision in the trace.

**Targeted tests**

- [ ] A transient news/provider failure follows the configured fallback route.
- [ ] A report contract failure never retries as a network error.
- [ ] Input-guard and privacy failures terminate without downstream tool calls.
- [ ] Retry exhaustion produces a sanitized, auditable failure.

**Acceptance criteria**

- Every terminal failure has a stable category and a documented next action.
- No node can retry indefinitely.

### SRAG-V2-102 — Add durable checkpoint and resume

**Priority:** P1  
**Dependencies:** SRAG-V2-101

**Tasks**

- [ ] Select and document a local checkpoint backend suitable for the demo.
- [ ] Persist checkpoints after externally expensive or durable steps.
- [ ] Resume an interrupted run by `run_id` without repeating completed
  deterministic work.
- [ ] Define checkpoint schema versioning and invalidation rules.
- [ ] Redact secrets and untrusted full-page content from checkpoint payloads.

**Targeted tests**

- [ ] Interrupt a fixture run after metrics and resume it.
- [ ] Verify that completed metric and chart tools are not called twice.
- [ ] Verify that an incompatible checkpoint version fails safely.

**Acceptance criteria**

- A controlled interruption can be resumed with equivalent final artifacts.
- Resume behavior is visible in the audit trace.

### SRAG-V2-103 — Make tool contracts explicit

**Priority:** P1  
**Dependencies:** SRAG-V2-100

**Tasks**

- [ ] Define typed input and output contracts for metric, chart, news, retrieval,
  report-validation, and persistence tools.
- [ ] Validate contracts at node boundaries.
- [ ] Add provenance fields to every evidence-bearing tool result.
- [ ] Prevent arbitrary tool selection from bypassing the fixed safety policy.

**Acceptance criteria**

- Malformed tool results fail at the producing node, not later during report
  rendering.
- Every external statement available to the writer carries source metadata.

**Phase 1 exit gate**

- [ ] The compiled LangGraph workflow is the only production execution path.
- [ ] Conditional routing, bounded retries, and failure tests pass.
- [ ] Checkpoint/resume is demonstrated with a fixture run.

---

## Phase 2 — Retrieval, Grounding, and Citation Provenance

### SRAG-V2-200 — Establish an honest lexical retrieval baseline

**Priority:** P0  
**Dependencies:** SRAG-V2-002

**Tasks**

- [ ] Rename `LocalVectorStore` and related public labels to reflect lexical
  retrieval, or temporarily place it behind a neutral `DocumentIndex` interface.
- [ ] Add stable document IDs, chunk IDs, source versions, ingestion timestamps,
  and content hashes.
- [ ] Build a curated retrieval set with questions about methodology, metric
  definitions, limitations, and DataSUS fields.
- [ ] Record Recall@5, Mean Reciprocal Rank, latency, and zero-result rate.

**Acceptance criteria**

- The baseline dataset and scoring script are reproducible.
- Results are stored under `artifacts/benchmarks/retrieval/`.
- No UI or documentation calls lexical search a vector store.

### SRAG-V2-201 — Implement a BM25 lexical retriever

**Priority:** P1  
**Dependencies:** SRAG-V2-200

**Tasks**

- [ ] Replace raw token-frequency overlap with a standard BM25 implementation.
- [ ] Normalize Portuguese accents and preserve medically meaningful tokens.
- [ ] Add deterministic tie-breaking and configurable `top_k`.
- [ ] Compare quality and latency with the Phase 2 baseline.

**Acceptance criteria**

- BM25 does not regress Recall@5 on the curated set.
- The benchmark records both quality and latency, not only anecdotal examples.

### SRAG-V2-202 — Add an optional dense retrieval backend

**Priority:** P1  
**Dependencies:** SRAG-V2-200

**Tasks**

- [ ] Add a provider-neutral embedding interface.
- [ ] Provide at least one local/offline embedding implementation suitable for
  reproducible tests.
- [ ] Persist embedding model identity, dimension, version, and document hash.
- [ ] Rebuild stale embeddings when content or model identity changes.
- [ ] Keep the lexical backend available when embeddings are unavailable.

**Acceptance criteria**

- Dense retrieval can be disabled without breaking report generation.
- Tests never require paid API credentials.
- Index compatibility is validated before search.

### SRAG-V2-203 — Implement and evaluate hybrid retrieval

**Priority:** P1  
**Dependencies:** SRAG-V2-201, SRAG-V2-202

**Tasks**

- [ ] Combine lexical and dense candidates using a documented fusion method.
- [ ] Preserve component scores for auditability.
- [ ] Add filters for source type, date, and document version.
- [ ] Compare lexical, dense, and hybrid modes on the same curated dataset.
- [ ] Select the default using measured quality, latency, and operational cost.

**Acceptance criteria**

- The default retriever improves Recall@5 or MRR over the Phase 2 baseline
  without violating the documented latency budget.
- If hybrid retrieval does not improve the benchmark, it remains optional and
  the result is reported honestly.

### SRAG-V2-204 — Enforce source-level citation provenance

**Priority:** P0  
**Dependencies:** SRAG-V2-200, SRAG-V2-103

**Tasks**

- [ ] Represent citations with source URL or path, title, publication date,
  retrieval timestamp, chunk ID, content hash, and supporting excerpt.
- [ ] Map each externally supported report claim to one or more citations.
- [ ] Reject fabricated, missing, disallowed, or unreachable citation
  references.
- [ ] Render a human-readable sources section and a machine-readable citation
  artifact.
- [ ] Distinguish official data, institutional documents, journalism, and
  generated interpretation.

**Acceptance criteria**

- Every externally supported claim in the evaluation set has a resolvable
  citation.
- Citation validation runs before report persistence.
- The audit artifact can trace a report statement back to the retrieved chunk.

**Phase 2 exit gate**

- [ ] Retrieval terminology is truthful.
- [ ] Lexical, dense, and hybrid results are measured on the same dataset.
- [ ] The selected default is justified by evidence.
- [ ] Citation provenance is enforced, not merely prompted.

---

## Phase 3 — Evaluation and Guardrail Hardening

### SRAG-V2-300 — Create the SRAG evaluation corpus

**Priority:** P0  
**Dependencies:** SRAG-V2-000

**Tasks**

- [ ] Add synthetic or safely derived fixtures for normal, sparse, malformed,
  and edge-case epidemiological data.
- [ ] Add expected metric outputs with methodological explanations.
- [ ] Add expected report requirements, acceptable limitations, and forbidden
  claims.
- [ ] Add retrieval questions with relevant document and chunk labels.
- [ ] Version the corpus and document how cases are reviewed.

**Acceptance criteria**

- Evaluation fixtures contain no personal or row-level real patient data.
- Every case has a stable ID, purpose, inputs, and expected checks.

### SRAG-V2-301 — Add metric and methodological regression tests

**Priority:** P0  
**Dependencies:** SRAG-V2-300

**Tasks**

- [ ] Cover zero denominators, unknown values, missing dates, duplicated records,
  late records, small groups, and empty time windows.
- [ ] Verify that UTI and vaccination outputs are labeled as case proportions.
- [ ] Verify timezone and period-boundary behavior.
- [ ] Add property-based tests for invariants where useful.
- [ ] Ensure the LLM cannot alter deterministic metric values.

**Acceptance criteria**

- All catalogued metrics have normal and edge-case tests.
- The generated report contains the exact deterministic metric values supplied
  by tools.

### SRAG-V2-302 — Build a prompt-injection and unsafe-content suite

**Priority:** P0  
**Dependencies:** SRAG-V2-300

**Tasks**

- [ ] Add malicious user prompts covering instruction override, secret
  extraction, unrestricted SQL, medical advice, and data exfiltration.
- [ ] Add malicious retrieved pages and news excerpts with embedded
  instructions.
- [ ] Add benign but unusual requests to measure false positives.
- [ ] Verify that untrusted content is treated only as evidence.
- [ ] Record block reason and guardrail stage without echoing sensitive content.

**Acceptance criteria**

- All known malicious cases are blocked or safely neutralized.
- The benign false-positive rate is measured and remains below the documented
  release threshold.
- Retrieved prompt injection cannot modify system policy or tool routing.

### SRAG-V2-303 — Add groundedness and report-contract evaluation

**Priority:** P0  
**Dependencies:** SRAG-V2-204, SRAG-V2-300

**Tasks**

- [ ] Check required sections, source presence, limitations, chart references,
  metric consistency, and forbidden medical claims.
- [ ] Add claim-to-evidence coverage and unsupported-claim checks.
- [ ] Use deterministic validators as the release gate.
- [ ] Keep model-based judging optional, versioned, and separate from the
  deterministic score.
- [ ] Store per-case and aggregate results.

**Acceptance criteria**

- A report with a correct format but unsupported factual claims fails.
- A report with correct prose but changed metric values fails.
- Release results show pass rate by category, not only one aggregate score.

### SRAG-V2-304 — Add controlled dependency-failure scenarios

**Priority:** P1  
**Dependencies:** SRAG-V2-101, SRAG-V2-300

**Tasks**

- [ ] Simulate DataSUS unavailability, malformed CSV, news timeout, embedding
  failure, LLM timeout, PDF failure, and disk write failure.
- [ ] Verify retry, fallback, checkpoint, and safe terminal behavior.
- [ ] Ensure partial runs cannot be presented as validated final reports.
- [ ] Add operator-facing remediation messages.

**Acceptance criteria**

- Every external dependency has at least one tested failure mode.
- Terminal status differentiates completed, completed-with-warning, and failed.

### SRAG-V2-305 — Add evaluation gates to continuous integration

**Priority:** P1  
**Dependencies:** SRAG-V2-301, SRAG-V2-302, SRAG-V2-303

**Tasks**

- [ ] Run fast deterministic tests on each pull request.
- [ ] Run the offline evaluation corpus without paid credentials.
- [ ] Publish a compact machine-readable evaluation summary.
- [ ] Add a scheduled or manually triggered network integration workflow.
- [ ] Prevent quality thresholds from silently decreasing.

**Acceptance criteria**

- Pull requests fail when deterministic metrics, guardrails, citations, or
  report contracts regress.
- Network-dependent failures are reported separately from offline regressions.

**Phase 3 exit gate**

- [ ] Metric, safety, groundedness, and dependency-failure suites pass.
- [ ] Evaluation evidence is reproducible without paid services.
- [ ] Quality thresholds and known limitations are public.

---

## Phase 4 — Observability, Audit, and Reviewer Experience

### SRAG-V2-400 — Define a versioned run-observability schema

**Priority:** P1  
**Dependencies:** SRAG-V2-100

**Tasks**

- [ ] Define run, node, tool, provider, retry, checkpoint, validation, and
  artifact events.
- [ ] Include duration, status, attempt, sanitized error category, input/output
  summary hashes, and parent-child relationships.
- [ ] Add schema version and forward-compatible readers.
- [ ] Define redaction rules for secrets, personal data, prompts, and retrieved
  content.

**Acceptance criteria**

- A run timeline can be reconstructed from the event stream.
- Event validation rejects malformed or secret-bearing payloads.

### SRAG-V2-401 — Instrument the full report pipeline

**Priority:** P1  
**Dependencies:** SRAG-V2-400

**Tasks**

- [ ] Instrument data loading, metrics, charts, retrieval, news, LLM calls,
  validation, PDF export, and persistence.
- [ ] Record provider and fallback decisions without storing credentials.
- [ ] Record token and monetary cost when available; use `unknown`, never a
  fabricated zero, when unavailable.
- [ ] Add correlation IDs across pipeline, graph, and artifacts.
- [ ] Optionally export OpenTelemetry-compatible traces behind configuration.

**Acceptance criteria**

- The timeline explains where time was spent and why a fallback occurred.
- Observability can be disabled without changing functional outputs.

### SRAG-V2-402 — Add a Streamlit run inspector

**Priority:** P1  
**Dependencies:** SRAG-V2-401

**Tasks**

- [ ] Add a run list with timestamp, status, duration, data version, and report
  validation status.
- [ ] Add a node timeline with retries and failure categories.
- [ ] Add metric, source, citation, data-quality, and artifact views.
- [ ] Add a clear separation between deterministic facts and LLM commentary.
- [ ] Prevent raw secrets and unsafe full retrieved content from rendering.

**Acceptance criteria**

- A technical reviewer can select one run and trace its report back to data,
  tools, retrieved evidence, and validations.
- The inspector works with committed fixture artifacts.

### SRAG-V2-403 — Add reproducible run comparison

**Priority:** P2  
**Dependencies:** SRAG-V2-401

**Tasks**

- [ ] Compare configuration, source versions, metrics, citations, validation,
  duration, and provider usage between two runs.
- [ ] Explain expected nondeterminism in LLM-authored prose.
- [ ] Add a machine-readable diff artifact.

**Acceptance criteria**

- Reviewers can identify whether a changed report came from data, configuration,
  retrieval, provider output, or code version.

**Phase 4 exit gate**

- [ ] A complete fixture run is inspectable from input metadata to final report.
- [ ] Trace schemas are versioned and redaction tests pass.

---

## Phase 5 — Reproducible Packaging and Delivery

### SRAG-V2-500 — Create a deterministic dependency installation path

**Priority:** P0  
**Dependencies:** SRAG-V2-000

**Tasks**

- [ ] Select and document one canonical dependency lock workflow.
- [ ] Separate runtime, development, and optional provider dependencies.
- [ ] Verify supported Python versions in CI.
- [ ] Add a clean-environment installation smoke test.
- [ ] Document native dependencies required for PDF or data processing.

**Acceptance criteria**

- The same documented command installs a clean development environment.
- Tests do not depend on undeclared globally installed packages.

### SRAG-V2-501 — Add a production-like container

**Priority:** P1  
**Dependencies:** SRAG-V2-500

**Tasks**

- [ ] Add a multi-stage Dockerfile with a non-root runtime user.
- [ ] Add health checking and configurable data/artifact volumes.
- [ ] Keep credentials runtime-only.
- [ ] Add `.dockerignore` rules for datasets, secrets, caches, and run artifacts.
- [ ] Add a fixture-mode container smoke test.

**Acceptance criteria**

- The container builds from a clean clone and serves Streamlit successfully.
- The image contains no `.env`, Git credentials, downloaded datasets, or test
  caches.

### SRAG-V2-502 — Add continuous integration

**Priority:** P0  
**Dependencies:** SRAG-V2-500

**Tasks**

- [ ] Add jobs for formatting checks, lint, type checking, targeted unit tests,
  offline integration tests, and security-sensitive guardrail tests.
- [ ] Cache dependencies without caching secrets or generated datasets.
- [ ] Add dependency and secret scanning.
- [ ] Upload compact test/evaluation summaries on failure.
- [ ] Add a container build check after fast jobs pass.

**Acceptance criteria**

- A pull request cannot merge with failed lint, typing, deterministic tests, or
  offline evaluation gates.
- The workflow never requires provider secrets for its default path.

### SRAG-V2-503 — Provide one-command fixture and real-data demos

**Priority:** P0  
**Dependencies:** SRAG-V2-500

**Tasks**

- [ ] Add a fixture demo that requires no credentials or network.
- [ ] Add a real-data demo with explicit download size, duration, and source
  warnings.
- [ ] Validate configuration and missing credentials before starting work.
- [ ] Print the report, trace, and dashboard locations at completion.
- [ ] Make repeated fixture execution idempotent.

**Acceptance criteria**

- A reviewer can generate and inspect a fixture report with one documented
  command.
- The real-data command fails early with actionable configuration guidance.

### SRAG-V2-504 — Harden public operational defaults

**Priority:** P1  
**Dependencies:** SRAG-V2-501, SRAG-V2-503

**Tasks**

- [ ] Add network timeout, maximum download size, maximum document size, retry,
  and concurrency limits.
- [ ] Add artifact retention and cleanup guidance.
- [ ] Validate allowlist redirects and final destination domains.
- [ ] Pin or hash trusted fixture inputs.
- [ ] Generate a dependency inventory or SBOM for releases.

**Acceptance criteria**

- Network operations are bounded.
- Redirects cannot bypass the source allowlist.
- Release artifacts include dependency provenance.

**Phase 5 exit gate**

- [ ] Clean-clone installation, CI, container, and fixture demo pass.
- [ ] Real-data execution is documented and bounded.

---

## Phase 6 — Public Portfolio and Open-Source Release

### SRAG-V2-600 — Rewrite the README as a technical landing page

**Priority:** P0  
**Dependencies:** Phases 1–5

**Tasks**

- [ ] Lead with the public-health problem and architectural differentiator.
- [ ] Add a 60-second quick start using fixtures.
- [ ] Add current architecture and report-flow diagrams.
- [ ] Add screenshots of the report, run inspector, sources, and data-quality
  views.
- [ ] Add measured test, evaluation, retrieval, and real-run evidence.
- [ ] Add limitations, safety boundaries, roadmap, and contribution links.

**Acceptance criteria**

- All badges and metrics link to reproducible evidence.
- No planned feature is written in the present tense.
- The README can be understood without reading the original challenge.

### SRAG-V2-601 — Create a concise demonstration video

**Priority:** P1  
**Dependencies:** SRAG-V2-600

**Tasks**

- [ ] Script a three-to-five-minute demo.
- [ ] Show data provenance, deterministic metrics, the graph timeline, retrieved
  citations, validation, and final report.
- [ ] Include one controlled unsafe-input or failure example.
- [ ] Add captions and an English summary for international accessibility.
- [ ] Link the video and a static fallback walkthrough from the README.

**Acceptance criteria**

- The video demonstrates implemented behavior from a clean fixture run.
- No secret, personal data, or unlicensed content is shown.

### SRAG-V2-602 — Publish a technical case study

**Priority:** P1  
**Dependencies:** SRAG-V2-600

**Tasks**

- [ ] Describe the problem, constraints, architecture, trade-offs, and evaluation
  method.
- [ ] Explain why deterministic computation is separated from generative text.
- [ ] Present measured results and failed experiments, including retrieval
  comparisons.
- [ ] Explain proxy metrics and public-health limitations.
- [ ] Provide reproducibility instructions and artifact links.

**Acceptance criteria**

- The case study contains evidence, not only architecture claims.
- Results are dated and tied to a Git commit and environment.

### SRAG-V2-603 — Prepare the first public release

**Priority:** P0  
**Dependencies:** SRAG-V2-600, SRAG-V2-601, SRAG-V2-602

**Tasks**

- [ ] Run the full release checklist.
- [ ] Confirm license, attribution, data policy, and security contacts.
- [ ] Remove challenge-only, secret, temporary, and oversized artifacts.
- [ ] Publish versioned release notes with known limitations.
- [ ] Create beginner-friendly issues only after their scope and acceptance
  criteria are documented.

**Acceptance criteria**

- The release can be installed and demonstrated from its tag.
- Release notes link to evaluation and benchmark evidence.
- GitHub’s default branch contains no secret or downloaded patient-level data.

**Phase 6 exit gate**

- [ ] A reviewer can understand, run, inspect, and verify the project.
- [ ] Public claims are backed by artifacts or tests.
- [ ] The repository is ready to be linked from a résumé.

---

## Phase 7 — Optional Research and Product Extensions

These tasks are explicitly optional. They must not delay the public release or
weaken the clarity of the core case study.

### SRAG-V2-700 — Add scheduled report generation

**Priority:** P2  
**Dependencies:** SRAG-V2-603

**Tasks**

- [ ] Add an idempotent scheduled-run command.
- [ ] Detect unchanged upstream data and skip unnecessary regeneration.
- [ ] Produce a run summary and safe failure notification.
- [ ] Keep publication or distribution human-approved by default.

**Acceptance criteria**

- Repeated execution against the same source version does not create duplicate
  reports unless explicitly requested.

### SRAG-V2-701 — Add report-over-report epidemiological change analysis

**Priority:** P2  
**Dependencies:** SRAG-V2-403, SRAG-V2-603

**Tasks**

- [ ] Compare deterministic metrics and data-quality changes across periods.
- [ ] Generate a structured change artifact before any narrative summary.
- [ ] Distinguish data revision from a genuine period change.
- [ ] Cite both compared source versions.

**Acceptance criteria**

- The system never attributes a difference to epidemiological change when it can
  only establish a source-data revision.

### SRAG-V2-702 — Evaluate human review feedback

**Priority:** P2  
**Dependencies:** SRAG-V2-603

**Tasks**

- [ ] Define structured reviewer feedback for accuracy, clarity, relevance,
  citation usefulness, and limitations.
- [ ] Keep feedback separate from authoritative epidemiological truth.
- [ ] Use feedback to propose evaluation cases, not to silently change safety
  policy or metric definitions.

**Acceptance criteria**

- Feedback lineage and resulting evaluation changes are auditable.

### SRAG-V2-703 — Investigate additional official data sources

**Priority:** P2  
**Dependencies:** SRAG-V2-603

**Tasks**

- [ ] Write a source contract for any proposed hospital capacity, vaccination,
  population, or regional data.
- [ ] Evaluate licensing, update cadence, schema stability, coverage, and
  denominator validity.
- [ ] Add the source only after deterministic reconciliation and quality tests.
- [ ] Update limitations and metric definitions before public use.

**Acceptance criteria**

- New sources improve a precisely defined metric and do not blur proxy and
  population-level interpretations.

---

## 5. Recommended Pull Request Sequence

1. **PR 1 — Baseline and truthful documentation:** SRAG-V2-000 to 003.
2. **PR 2 — Real graph execution:** SRAG-V2-100 and 103.
3. **PR 3 — Routing and resume:** SRAG-V2-101 and 102.
4. **PR 4 — Retrieval baseline and citations:** SRAG-V2-200 and 204.
5. **PR 5 — Retrieval experiments:** SRAG-V2-201 to 203.
6. **PR 6 — Evaluation corpus and deterministic gates:** SRAG-V2-300 to 303.
7. **PR 7 — Failure testing and CI evaluation:** SRAG-V2-304 and 305.
8. **PR 8 — Observability:** SRAG-V2-400 and 401.
9. **PR 9 — Run inspector and comparison:** SRAG-V2-402 and 403.
10. **PR 10 — Packaging and CI:** SRAG-V2-500 to 504.
11. **PR 11 — Public release assets:** SRAG-V2-600 to 603.

## 6. Final Release Scorecard

| Area | Required evidence | Release requirement |
|---|---|---|
| Architecture | Executed graph trace and diagrams | Compiled LangGraph is the only production path |
| Metrics | Deterministic regression suite | All metric and edge-case tests pass |
| Retrieval | Versioned benchmark | Default selected from measured lexical/dense/hybrid comparison |
| Grounding | Claim-to-citation artifact | All evaluated external claims have resolvable evidence |
| Safety | Adversarial corpus | Known malicious cases blocked or neutralized |
| Reliability | Failure-injection suite | Bounded retry, fallback, resume, and safe terminal states pass |
| Observability | Inspectable fixture run | Data, tools, sources, decisions, and artifacts are traceable |
| Reproducibility | Clean-clone and container runs | Fixture demo works without paid credentials |
| Public communication | README, video, case study | No unsupported or future-tense-as-present claims |
| Data governance | Repository and release scan | No secrets or patient-level downloaded data committed |

## 7. Explicit Non-Goals for V2

- Clinical diagnosis or individualized medical advice.
- Autonomous publication of public-health alerts.
- Free-form SQL generated and executed by an LLM.
- Replacing official epidemiological surveillance.
- A generic multi-agent platform.
- Adding many model providers without a measured reliability need.
- Claiming hospital occupancy or population vaccination coverage from
  case-level proxy fields.
- Using an LLM-based judge as the only release gate.
