# Materials Simulation Skill Protocol

A small, opinionated standard layered on top of the open
[Agent Skills specification](https://agentskills.io/specification). The base spec
says what a skill *is*; this protocol says what a skill in **this** repository must
do to be **portable, composable, and scientifically trustworthy**.

Conformance is enforced where it can be (CI: `mss validate`, `mss eval`,
`skills-ref`) and documented where judgment is required. A skill that passes the
checklist below is *protocol-conformant*.

---

## Why a protocol

The skill audit found that the largest defect class was **documentation drifting
from code** — worked examples with wrong numbers, output-field tables that no
longer matched the scripts, Security sections promising safeguards the code
didn't implement. The conventions here exist to make that class of defect
*structurally hard to reintroduce*: every numeric claim is pinned by a test,
every safeguard is documented in a fixed shape, and the science is cited.

---

## Conformance checklist

### 1. Spec-valid frontmatter  *(enforced — `mss validate`)*

- `name`: 1–64 chars, lowercase `a–z`, `0–9`, and `-`; no leading/trailing or
  consecutive hyphens; **matches the directory name**.
- `description`: non-empty, ≤ 1024 chars; says **what** the skill does **and when**
  to use it (the primary triggering signal — keep it specific and a little
  "pushy" to avoid under-triggering).
- A `metadata:` block is present.
- `compatibility:` (optional, ≤ 500 chars) — use it to declare real environment
  needs (Python version, NumPy/SciPy, network), rather than burying them in prose.

### 2. Script I/O envelope  *(verified — integration tests + `script_checks`)*

Every script is a standalone CLI with:

- `--json` emitting `{ "inputs": {...}, "results": {...}, "notes": [ ... ] }`
  (or a documented superset). Field names are stable and documented in `SKILL.md`.
- `--help` (argparse) and a `__main__` guard.
- Exit codes: **`2`** on bad input (with a clear stderr message), **`1`** on
  runtime error, **`0`** on success.
- A pure-function core, importable for unit testing, separate from the CLI shell.

### 3. Cited science  *(reviewed)*

Rules, thresholds, and formulas name the authoritative source they come from
(e.g. ASME V&V20 for GCI, the SchedMD `sbatch` spec for SLURM, CMSO IRIs for
ontology terms), in `SKILL.md` or `references/`, so an agent can *defend* an
answer rather than only produce it. Worked-example numbers must be correct.

### 4. Standardized Security section  *(enforced — `mss validate`)*

A `## Security` section with exactly these four `###` subsections, each
describing only what the code actually does (no aspirational claims):

- **Input Validation** — bounds/finite/allowlist checks; exit `2` on bad input.
- **File Access** — which files are read/written, size limits, sandboxing caveats.
- **Tool Restrictions** — what each `allowed-tools` entry is used for.
- **Safety Measures** — no `eval`/`exec`, explicit subprocess arg lists, DoS caps.

The repo classifies each skill by tool-access tier (HIGH = has `Bash`, MEDIUM =
`Write` only, LOW = read-only). A skill either declares the `Bash` it needs to run
its scripts, or it ships logic the agent applies without execution — never both
stories at once.

### 5. Evaluation suite  *(enforced — `mss validate` + `mss eval`)*

- `evals/evals.json` with ≥ 3 realistic cases, each with `assertions`.
- Every case whose answer is computable carries deterministic
  [`script_checks`](EVAL_HARNESS.md) that pin the script's exact output. The repo
  target is **100 % of computable cases covered**; cases left LLM-judge-only are
  the genuinely advisory ones.
- Fixtures live in `evals/files/`; **generated outputs are not committed** (write
  them to a git-ignored `evals/scratch/` or ignore the specific generated file).

### 6. Versioning & provenance  *(reviewed)*

- Semantic version in `metadata.version`; a `CHANGELOG.md` entry per change.
- `metadata.last_evaluated` records when the skill was last exercised end-to-end.
- Numeric `results` carry units (in `notes` or a `units` map); outputs destined
  for FAIR packaging expose engine/version/standard identifiers.

### 7. Progressive disclosure  *(reviewed)*

`SKILL.md` stays focused (< 500 lines); deep tables and catalogs go in
`references/`, loaded on demand with an explicit "read X when Y" pointer.

### 8. Composition  *(emerging)*

A skill may declare sibling skills it builds on via `metadata.depends_on`,
enabling a dependency graph and curated "bundles". Skills should reference and
reuse each other rather than duplicate logic.

---

## Validating conformance

```bash
mss validate          # frontmatter, name rules, Security subsections, evals, changelog
mss eval              # every deterministic script_check passes (doc<->code drift gate)
python -m pytest tests/   # script correctness (unit) + CLI/JSON schema (integration)
```

For base-spec conformance, also run the official reference validator
([`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref)):

```bash
skills-ref validate skills/<category>/<skill>
```

CI runs `mss validate` and `mss eval` on every push (the `validate-quality` job),
and the test matrix on Python 3.10–3.12. New or changed skills must pass all of
the above before merge.
