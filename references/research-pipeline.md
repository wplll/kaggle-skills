# Research Pipeline

Use this reference when the user provides a Kaggle competition slug and wants automated research, baseline selection, optimization design, implementation, submission guidance, or ongoing monitoring.

## Intake

Collect:

- competition slug
- user goal: research only, implement baseline, optimize, push, submit, or watch
- whether the user has accepted competition rules
- whether CLI credentials are configured
- allowed automation boundary for submissions and public publishing

If rules acceptance, private datasets, or workspace attachments are missing, report the blocker and continue with public metadata where possible.

## Competition Discovery

Gather:

- title and slug
- task type
- metric
- deadline and stage
- submission mode: file upload, notebook/kernel, simulation, or other
- rules and external data policy
- runtime, internet, GPU/TPU, RAM, and storage constraints
- competition files and sample submission shape

Prefer official Kaggle CLI/API. If a page is only visible in the browser, summarize that manual access is required.

If local `kaggle.exe` crashes with no output, retry through `python -m kaggle.cli` from a Python environment with the `kaggle` package installed. This occurs on some Windows/Anaconda installs.

## Code Collection

Collect public kernels associated with the competition. Query multiple sorts because one ranking is biased:

- `voteCount`: community consensus
- `scoreDescending`: leaderboard-facing candidates when available
- `commentCount`: active discussion and debugging
- `dateRun`: recent changes
- `relevance`: targeted searches such as baseline, ensemble, cv, postprocess, leak

For each candidate, record:

- `owner/slug`
- title
- author
- votes/comments/views/score/run date when available
- language and kernel type
- output files when available
- whether `kaggle kernels pull <owner>/<slug> -m` succeeds
- metadata sources: datasets, kernels, models, competitions
- core method summary
- dependency access risk
- estimated runtime risk
- reproducibility risk

Do not rank by public score alone. Penalize private dependencies, inaccessible datasets, stale notebooks, hidden external data, fragile paths, and excessive runtime.

## Discussion Collection

Collect topics and selected messages. Use broad sorts first, then keyword searches.

The installed Kaggle CLI may not expose Discussion commands even when upstream docs mention them. If `kaggle competitions topics ...` is unavailable, use the read-only JSON fallback:

1. Call `https://www.kaggle.com/api/i/competitions.CompetitionService/GetCompetition?competitionName=<slug>` and read `forumId`.
2. Call `https://www.kaggle.com/api/i/discussions.DiscussionsService/GetTopicListByForumId?forumId=<forumId>&page=1`.
3. Archive high-signal topic details with `GetForumTopicById?forumTopicId=<topicId>&includeComments=true`.
4. Store raw JSON under `research/<slug>/raw/`.

Important sorts:

- hot/top for durable community consensus
- new/recent/active for changes and late discoveries

Important keywords:

- baseline
- LB
- CV
- metric
- leak
- rule
- external data
- submission
- timeout
- OOM
- notebook
- kernel

Classify discussion findings as:

- host clarification
- rule or data change
- scoring or metric insight
- CV/LB mismatch
- leak claim
- shared baseline or trick
- failure mode
- resource or sandbox issue
- speculation

Separate facts from claims. Mark compliance-sensitive items for user review.

Prefer archiving details for:

- host posts
- submission/how-to-submit threads
- metric or class-scope threads
- external data/license threads
- timeout/OOM/missing data threads
- score claims such as "single model 0.xxx"
- pseudo-labeling/CV/LB mismatch threads

## Past Editions And Similar Competitions

Run this stage when the competition is recurring (year-suffixed slug), sits in a well-studied domain, or has a quiet current-edition forum. Past editions usually publish more credible solution writeups than the current edition's early-phase chatter.

Use `scripts/past_competitions.py`:

- `--past <slug>` for explicit prior or sibling competitions (repeatable)
- `--auto-years` plus `--years LO HI` to expand `<base>-YYYY` siblings
- `--search <keyword>` for topical sibling discovery
- `--include-current` if you want the current slug archived for parity

Output goes under `research/<base>/past/` with `index.md`, `past_state.json`, and per-slug `summary.md` plus `raw/` archives. The script ranks Discussion topics by solution-writeup signal (1st/2nd/3rd place, winning solution, writeup, hot keywords, HOST author, votes) and saves the top N to `topic_details/`.

When transferring tricks across editions, verify:

- metric parity
- data scope and external-data policy
- runtime budget
- test/submission shape

Fold cross-edition findings into `report.md` under a "Cross-Edition Lessons" section. Do not promote a past-edition winner directly into the current `optimization_plan.md`; treat it as evidence for selecting a current-edition baseline. See `past-competitions.md` for the full workflow.

## Report

Write `research/<competition-slug>/report.md` with:

1. Collection timestamp and environment.
2. Competition overview and API facts such as deadline, Kernel-only flag, runtime limits, metric, submission filename, row id column, daily quota, and license.
3. Rules and sandbox constraints.
4. Data/files and sample submission notes.
5. Top Code candidate table.
6. Discussion findings.
7. Best open baseline recommendation.
8. Optimization opportunities.
9. Risks and blockers.
10. Next execution plan.

Every important claim needs a Kaggle URL, CLI output archive path, or local pulled file path.

When report generation finds a promising baseline, the agent should still create a separate `optimization_plan.md` after pulling and inspecting that baseline. Do not confuse a ranked Code table with a verified implementation plan.

## Baseline Selection

Choose the baseline that best balances:

- reproducible source
- accessible dependencies
- clean metadata
- available output/submission path
- high score or high-quality community validation
- manageable runtime
- simple patch surface
- rule compliance

Default plan:

- Phase 0: replay baseline with minimal changes.
- Phase 1: one low-risk optimization.
- Phase 2+: one variable per phase.

## Implementation Gate

Before implementation, produce `optimization_plan.md` with:

- selected baseline and why
- rejected candidates and why
- phase table
- expected gain
- runtime cost
- rollback plan
- validation markers
- submission gate

Do not stack unrelated changes before a baseline replay.

## Monitoring

Maintain `state.json`:

- `last_checked_at`
- `seen_kernel_refs`
- `seen_topic_ids`
- `seen_comment_ids`
- `selected_baseline`
- `experiment_history`
- `known_blockers`
- `watch_keywords`

On update:

- fetch new kernels and topics
- summarize deltas
- decide whether the new content changes the plan
- update report and optimization plan
- propose new phases, but do not submit without confirmation
