# RULES-PYTHON-V3 -- Python 3.12 Development Standards

**Target:** Python 3.12 preferred, 3.11 minimum. macOS/zsh and Ubuntu/bash. Governs all Python application types: services, CLIs, pipelines, dashboards, desktop tools, ML workflows.
**Deep-dive reference:** `references/python-best-practices.md` (examples, antipatterns, silent-error landmines, library configs)

---

## PART 1: FIRST PRINCIPLES

Precedence: P1 overrides all. Each principle overrides all subsequent ones.

| #   | Principle                    | Rule                                                                                                                      |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| P1  | Fix Over Create              | Modify existing code; create new file only when `radon cc` returns grade C or higher. No grade C or lower. Refactor; never average. |
| P2  | Reusable Testing             | No one-off scripts; single quality utility in `src/scripts/`; tests in `tests/`                                          |
| P3  | Docs Location                | All docs in `docs/`; sole exception: `CLAUDE.md` at root                                                                  |
| P4  | Never Defer                  | Clean code first priority; no "fix later"; no "out of scope"; no "unrelated"; hard work now                              |
| P5  | Use Agents                   | Parallel context windows; always use for non-dependent tasks                                                              |
| P6  | Anti-Elision                 | Exhaustive generation required. Stubs/truncation/`...`/`pass`/`# TODO` prohibited                                        |
| P7  | Contextual Strictness        | Pre-authoring source inspection mandatory. Zero assumption of signatures/state. Read before write                        |
| P8  | Explicit Failure Propagation | Zero exception swallowing. Boundary validation -> immediate custom exceptions. `None` signals absence, not failure        |
| P9  | Idempotent Mutation          | Execution multiplicity -> identical state. Verify existing state pre-mutation                                             |
| P10 | Simplicity                   | Minimum complexity for current task; no premature abstraction; no patterns unless demonstrably required                  |
| P11 | Test Coverage                | 100% test coverage, 100% passing unit and E2E. < 100% = FAILURE                                                          |
| P12 | Never Reinvent the Wheel     | Prefer existing proven FOSS packages/software instead of writing new custom code                                          |

---

## PART 2: HARD CONSTRAINTS

### 2.1 Banned Patterns

**Elision (-> P6):** `pass`/`...` bodies, `raise NotImplementedError` (non-`@abstractmethod`), `# TODO`/`# placeholder` comments.

> Inability to implement -> state it in prose. Never emit placeholder code.

**Type annotation violations:**

```python
# BANNED -- use builtins + | syntax
from typing import List, Dict, Union, Optional
List[str]       # -> list[str]
Dict[str, int]  # -> dict[str, int]
Union[X, Y]     # -> X | Y
Optional[X]     # -> X | None
```

**Security violations (all BANNED):**

| Pattern                                           | Risk           | Replacement                                                  |
| ------------------------------------------------- | -------------- | ------------------------------------------------------------ |
| `pickle.loads(untrusted)`                         | RCE            | JSON + Pydantic schema                                       |
| `yaml.load()` without SafeLoader                  | RCE            | `yaml.safe_load()`                                           |
| `eval()`/`exec()`/`compile()` on user input       | RCE            | `ast.literal_eval()` or parser                               |
| `subprocess.run(cmd, shell=True)` with user input | Cmd injection  | List-form + `check=True`                                     |
| `os.system()`/`os.popen()`                        | Cmd injection  | `subprocess.run([], shell=False, check=True)`                |
| `random` for security tokens                      | Predictable    | `secrets.token_urlsafe(32)`                                  |
| f-string/format in SQLAlchemy `text()`            | SQLi           | Parameterized `text("... :param", {"param": val})`           |
| `verify=False` in HTTPX/requests                  | MitM           | Always `verify=True`                                         |
| `tempfile.mktemp()`                               | Race condition | `(fd, path) = tempfile.mkstemp(); os.close(fd)`              |
| `assert` for runtime validation                   | -O bypass      | `if/raise`                                                   |
| `__eq__` for secret comparison                    | Timing attack  | `hmac.compare_digest(a, b)` -- equal-length inputs only      |
| `xml.etree`/`lxml` with untrusted XML             | XXE            | `defusedxml`                                                 |
| `shelve`/`marshal`/`dill`/`jsonpickle` untrusted  | RCE            | Pydantic schema                                              |
| `datetime.utcnow()`                               | Naive datetime | `datetime.now(tz=datetime.timezone.utc)`                     |

**Also banned:** mutable defaults * bare `except:` * circular imports * global mutation * magic numbers * hardcoded secrets * unvalidated inputs * debugger remnants (`breakpoint()`/`pdb`/`ipdb`) * `print()` (-> structlog / `typer.echo` in CLI) * deprecated typing imports (`List`/`Dict`/`Union`/`Optional` -> builtins+`|`) * `poetry` (-> uv) * `tenacity` (-> stamina) * `tqdm` (-> rich.progress) * `requests` (-> HTTPX) * stdlib `logging` in application code (-> structlog) * `autopep8`/`docformatter` (-> ruff)

### 2.2 Complexity Limits

All enforced via ruff. Violations MUST be refactored before commit.

| Limit                            | Max | Ruff Rule |
| -------------------------------- | --- | --------- |
| Statements per function          | 50  | `PLR0915` |
| Cyclomatic complexity            | 10  | `C901`    |
| Parameters per function          | 5   | `PLR0913` |
| Return statements                | 6   | `PLR0911` |
| Branches per function            | 12  | `PLR0912` |
| Inheritance depth                | 3   | --        |
| Nesting levels (inside function) | 4   | --        |

### 2.3 Abstraction Limits

- No ABC/Protocol without 3+ concrete implementations extant now
- No passthrough wrappers (sole body = single delegating call)
- No class with `__init__` + one method -> function
- No stateless class -> module with functions

### 2.4 DRY Limits

- 4+ shared consecutive lines -> extract (named after function, not origin)
- Copy-paste + name/literal substitution -> parameterize
- Pre-authoring: search for >=80%-similar implementations; reuse/extend (-> P7)
- Single-use extraction only if readability gain is measurable
- Stdlib (`itertools`/`functools`/`collections`) before reimplementation

### 2.5 Design Principles

| Principle | Mandate                                                               |
| --------- | --------------------------------------------------------------------- |
| DRY       | Single implementation per concept; §2.4 enforces                      |
| SPOT      | One authoritative source per fact/config value                        |
| YAGNI     | No speculative features; build only what is needed now                |
| SOLID     | SR/OC/L/IS/DI; violated by God classes and deep inheritance           |
| GRASP     | Assign responsibility to the class with the most relevant information |

### 2.6 Package Management

- **uv ONLY** -- `uv init`, `uv add`, `uv run`, `uv sync --frozen`, `uv lock --universal`
- **`uv.lock` MUST be committed** and generated with `--universal` (cross-platform CI requires it)
- **poetry BANNED** -- do not create `pyproject.toml` with `[tool.poetry]`
- **pip BANNED for project management** -- use `uv pip` only if pip syntax is required in CI

---

## PART 3: STANDARDS

### 3.1 Project Structure

| Requirement     | Rule                                                                              |
| --------------- | --------------------------------------------------------------------------------- |
| Imports         | Absolute from source root only; no relative imports                               |
| Entry point     | `main.py` orchestrates only; no core logic; invoke via `python -m {project}.main` |
| Complexity gate | No file exceeds radon cc grade B; C/D/E MUST be refactored                        |

**Required files:** `docs/prd.md`, `docs/spec.md`, `checkpython.sh` (never modify), `.pre-commit-config.yaml`

**READ:** `docs/orientation.md` for project structure always.

### 3.2 Configuration

| Rule               | Detail                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| Config source      | `config.yml` -> settings; `credentials.yml` -> secrets                                             |
| Pydantic parsing   | `pydantic-settings` loads all config. **YAML is NOT built-in** -- requires `YamlConfigSettingsSource`; see ref §5.2 |
| Gitignore          | `credentials.yml` in `.gitignore`; ship `credentials.yml.dist` as template                         |
| Env-var bridge     | Env vars allowed ONLY via `pydantic-settings` `env_prefix`; never raw `os.environ`                 |
| Immutability       | Never overwrite user-set tokens/keys/passwords                                                      |
| Idempotency (-> P9)| Config setup must be re-runnable; verify state before mutation                                      |
| No hardcoding      | All values in config; none inline in code                                                           |

### 3.3 App Shape

Select the library set that matches your application type. One row per concern; default is the 2026 recommended pick.

| App Type              | Default                  | Alternatives / When                                                        |
| --------------------- | ------------------------ | -------------------------------------------------------------------------- |
| HTTP API / service    | FastAPI + uvicorn        | Starlette [custom ASGI middleware], Litestar [opinionated alt], Flask [legacy only] |
| Web UI / admin / forms| NiceGUI                  | Streamlit [data dashboards / ML], Reflex [full-stack Python + React], FastHTML [HTMX-style] |
| ML demo / Spaces      | Gradio                   | Streamlit [general dashboards]                                             |
| Desktop GUI           | PySide6 (LGPL)           | CustomTkinter [simple internal tools], Toga / Flet [cross-platform + mobile] |
| Terminal UI (interactive) | Textual              | Rich [output only; not interactive]                                        |
| Notebooks             | marimo                   | Jupyter [existing .ipynb / ecosystem compatibility]                        |

### 3.4 Type Hints (3.12 syntax)

```python
type Point = tuple[float, float]       # 3.12 type alias (PEP 695)
type Vector[T] = list[T]               # 3.12 generic alias
class Stack[T]: ...                    # 3.12 generic class
def first[T](lst: list[T]) -> T: ...  # 3.12 generic function

from typing import override, Self      # 3.12 stdlib (use typing_extensions on 3.11)
```

Always use:
```python
def process(items: list[str]) -> dict[str, int]: ...
def fetch(url: str) -> bytes | None: ...    # X | Y not Union[X, Y]
```

### 3.5 Core Libraries

| Domain                  | Default                   | Alternatives / Notes                                                    |
| ----------------------- | ------------------------- | ----------------------------------------------------------------------- |
| Package mgmt            | uv                        | ONLY; poetry BANNED                                                     |
| Validation              | Pydantic v2               | `strict=True`, `extra="forbid"` for internal models; `extra="ignore"` for external API models |
| Config loading          | pydantic-settings         | Custom `YamlConfigSettingsSource` required for YAML -- not built-in     |
| Database                | SQLAlchemy                | Core or ORM; no raw SQL strings                                         |
| Migrations              | Alembic                   | All schema changes; no manual DB modifications                          |
| HTTP client             | HTTPX                     | `AsyncClient`; never requests                                           |
| HTTP server             | FastAPI + uvicorn         | See §3.3; granian [high-perf Rust ASGI], hypercorn [HTTP/3]            |
| CLI                     | Typer                     | `typer.echo` for CLI output; not `print()`                              |
| Web UI                  | NiceGUI                   | See §3.3                                                                |
| Desktop GUI             | PySide6                   | See §3.3                                                                |
| Terminal UI             | Textual                   | Rich for output; Textual for interactive apps                           |
| Notebooks               | marimo                    | Jupyter for existing .ipynb compatibility                               |
| Logging                 | structlog + orjson        | NEVER stdlib logging; orjson MUST be wired as JSON serializer           |
| Console / progress      | rich                      | Tables, progress bars, tracebacks                                       |
| Retries                 | stamina                   | NEVER tenacity                                                          |
| JSON                    | orjson                    | All JSON; must be wired to structlog renderer                           |
| DataFrames              | polars                    | pandas acceptable for existing code only; not for new projects          |
| OLAP / SQL analytics    | DuckDB                    | Zero-copy with polars + PyArrow; reads Parquet/CSV directly             |
| Data interchange        | PyArrow                   | All Parquet I/O; cross-library exchange format                          |
| DataFrame validation    | pandera                   | Pydantic-native schema validation for DataFrames (pandas + polars)      |
| Numeric / scientific    | numpy + scipy             | Foundational; complement polars, do not replace it                      |
| ML (classical)          | scikit-learn              | Pipelines, preprocessing, evaluation                                    |
| ML (deep learning)      | PyTorch                   | Default DL; JAX for research / high-performance / custom kernels        |
| LLM / pretrained models | Hugging Face transformers | `datasets` + `peft` for fine-tuning; `accelerate` for distributed      |
| Visualization           | plotly                    | altair [notebooks / grammar-of-graphics], matplotlib [publication-quality], seaborn [statistical] |
| High-throughput serial. | msgspec                   | Data pipelines; also covers JSON/MessagePack/YAML                       |
| Background jobs         | arq                       | Celery [legacy / sync-heavy workloads], Dramatiq [sync alternative]    |
| Caching                 | redis-py / valkey-py      | `functools.cache` / `cachetools` for in-process                         |

### 3.6 Logging (structlog)

```python
import structlog
log = structlog.get_logger()

log.info("processing.complete", records=150, duration_s=3.2)
log.warning("rate_limit.approaching", usage_pct=85, limit=1000)
log.error("connection.failed", host="api.example.com", retries=3, exc_info=True)

log = log.bind(request_id="abc123", user_id=42)
```

**Rules:** No secrets/PII/request-body logging * `log.debug()` not `print()` * strip newlines from user strings (log-forging prevention) * orjson MUST be configured as the JSON serializer (default is stdlib json) * see ref §7.3 for `configure_logging()` with orjson wiring

### 3.7 Error Handling

-> P8: zero swallowing; `None` signals absence, not failure.

- Custom exception hierarchy per project
- `stamina` with `wait_initial`, `wait_max`, `wait_jitter` explicitly set for all retries
- `subprocess.run([...], check=True)` -- non-zero exit is silent without `check=True`
- `except Exception` MUST NOT expose stack traces to clients
- `bare except:` BANNED; `except Exception` requires logging at minimum

### 3.8 Security

```python
from pydantic import BaseModel, Field, ConfigDict, SecretStr
from typing import Annotated, Literal

class UserInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")   # internal models only
    username: Annotated[str, Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_]+$")]
    role: Literal["user", "admin", "viewer"]
    password: SecretStr   # prevents repr/log leaks; model_dump(mode='json') still emits cleartext
```

| Rule                              | Detail                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| Internal models                   | `strict=True`, `extra="forbid"` -- no coercion, no mass-assignment                 |
| External / partner-API models     | `extra="ignore"` -- accept new optional fields without breaking                     |
| Dynamic col/table names           | Allowlist validation before use; guard LIKE-pattern injection (`%`, `_`) too        |
| Secrets at rest                   | `credentials.yml` + `SecretStr` + `0600` perms + `detect-secrets` pre-commit hook  |
| File paths                        | `Path.resolve()` + base-dir check; default-deny                                    |
| Access control                    | Service-layer authz; not route decorators alone                                     |
| Password storage                  | `argon2-cffi`: `PasswordHasher().hash(pw)`, `.verify(h, pw)`, `.check_needs_rehash(h)` |
| Timing-safe comparison            | `hmac.compare_digest(a, b)` -- constant-time ONLY when `len(a) == len(b)`          |
| HTTP                              | `follow_redirects=False`; always `raise_for_status()`; SSRF: check `ip.is_private` post-DNS |

### 3.9 Testing

100% test coverage mandatory. < 100% = FAILURE.

```python
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100
```

```toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
asyncio_mode = "strict"    # when using pytest-asyncio
```

```toml
[tool.coverage.run]
branch = true
relative_files = true
```

| Category          | Tool                                                        |
| ----------------- | ----------------------------------------------------------- |
| Model validation  | Pydantic + pytest                                           |
| DB logic          | SQLAlchemy + test DB                                        |
| HTTP interactions | `pytest-httpx` (no real HTTP in unit tests)                 |
| Async             | `pytest-asyncio` (strict mode) or `anyio`                   |
| Migrations        | Alembic + pytest                                            |
| CLI               | Typer + pytest                                              |
| Time / clock      | `time-machine` or `freezegun`                               |
| Property-based    | `hypothesis` (parsing / validation)                         |
| Mutation          | `mutmut` (critical business logic; not required per-PR)     |

### 3.10 Progress & Reporting

**rich** for all progress/tables/tracebacks. Reports: HTML + Tailwind + chosen viz library (plotly / altair / matplotlib per §3.5); client-side rendering only.

---

## PART 4: QUALITY GATE

All three tiers are mandatory. Full configs: `references/python-best-practices.md §21`.

### Tier 1 -- Gate (Must Pass Before Every Commit)

| Tool      | Command                                            | Purpose                    |
| --------- | -------------------------------------------------- | -------------------------- |
| ruff      | `ruff check src/`                                  | Linting (800+ rules)       |
| ruff      | `ruff format --check src/`                         | Formatting                 |
| mypy      | `mypy --strict src/`                               | Type checking (strict mode)|
| pytest    | `pytest tests/ --cov=src --cov-fail-under=100`     | Tests + coverage           |
| deptry    | `deptry src/`                                      | Dependency analysis        |
| bandit    | `bandit -r src/`                                   | Security SAST              |
| pip-audit | `pip-audit`                                        | PyPI CVE scanning          |

### Tier 2 -- Quality Analysis (Mandatory)

| Tool           | Command                                       | Purpose                                    |
| -------------- | --------------------------------------------- | ------------------------------------------ |
| radon          | `radon cc src/ -a -nb`                        | Cyclomatic complexity                      |
| pyright        | `pyright src/`                                | Additional type checking (different catches than mypy) |
| semgrep        | `semgrep --config auto src/`                  | Security patterns (complements bandit)     |
| interrogate    | `interrogate src/`                            | Docstring coverage                         |
| osv-scanner    | `osv-scanner scan --lockfile uv.lock`         | Broader CVE feed than pip-audit            |
| detect-secrets | `detect-secrets scan`                         | Hardcoded secrets in source                |
| gitleaks       | `gitleaks detect`                             | Git history secret scanning                |

### Tier 3 -- Advanced (Mandatory)

| Tool       | Command / Usage                                   | Purpose                                          |
| ---------- | ------------------------------------------------- | ------------------------------------------------ |
| mutmut     | `mutmut run` (critical business logic)            | Mutation testing                                 |
| hypothesis | In test files via `@given`                        | Property-based testing                           |
| py-spy     | `py-spy record -o profile.svg -- python ...`      | Performance profiling                            |
| pandera    | Schema definitions in `tests/` or `src/`          | DataFrame validation                             |
| beartype   | `@beartype` on public APIs                        | Runtime type checking (pick ONE: beartype OR typeguard) |
| wily       | `wily build src/ && wily report`                  | Complexity trend tracking                        |

**Pruned (true redundancy -- not required):** `refurb` (ruff FURB covers it) * `xenon` (ruff C901 + radon cover cyclomatic complexity) * `pylint` (ruff PL* covers it) * `dodgy` (superseded by detect-secrets / gitleaks) * `cohesion` (high false-positive rate) * `vulture` (high false-positive rate) * `jscpd` (Node.js toolchain; wrong ecosystem)

### Ruff Configuration

```toml
[tool.ruff.lint]
select = [
  "E", "W",    # pycodestyle
  "F",         # pyflakes
  "B",         # bugbear
  "I",         # isort
  "UP",        # pyupgrade
  "TRY",       # exception handling
  "SIM",       # simplification
  "FURB",      # reimplemented stdlib (replaces refurb)
  "PIE",       # anti-elision (pass/..., unnecessary spread)
  "ARG",       # unused arguments
  "C901",      # cyclomatic complexity
  "PLR0911", "PLR0912", "PLR0913", "PLR0915",
  "S",         # security (bandit subset)
  "TCH",       # type-checking imports
  "D",         # pydocstyle
  "RET",       # return statement simplification
  "ERA",       # eradicate commented-out code
]

[tool.ruff.lint.pydocstyle]
convention = "google"    # REQUIRED -- omitting causes conflicting D rule violations

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5
max-returns = 6
max-branches = 12
max-statements = 50
```

---

## PART 5: 9-DIMENSION QA CHECKLIST

Apply to every PR before merge. Each dimension must be explicitly answered. "No issues" is a valid answer only if the dimension was actively checked.

| Dimension      | Question                                 | Pass Criteria                                    |
| -------------- | ---------------------------------------- | ------------------------------------------------ |
| Good           | What is working correctly?               | Enumerate; confirm no regressions introduced     |
| Bad            | What is broken or incorrect?             | Zero known breakage within PR scope              |
| Missing        | What functionality is absent?            | All spec requirements implemented                |
| Unnecessary    | What code/features are superfluous?      | No dead code; no over-engineering                |
| Fixed          | What was repaired in this change?        | All stated bugs resolved and test-confirmed      |
| Newly Broken   | What previously worked but now fails?    | Full test suite green; E2E passes                |
| Silent Errors  | What hidden failures exist?              | No swallowed exceptions; no bare `except`        |
| Overengineered | What is unnecessarily complex?           | Radon grade <= B; CC <= 10; params <= 5          |
| Dead           | What is technical debt or dead code?     | No TODO/FIXME/placeholder remnants               |

---

## PART 6: VUW METHODOLOGY

**Verifiable Units of Work** -- micro-plans for disciplined debugging.

| Element            | Rule                                                              |
| ------------------ | ----------------------------------------------------------------- |
| Granularity        | One file or one error per VUW                                     |
| Definition of Done | All checklist items pass                                          |
| Execution          | Sequential; complete before next VUW                              |
| Instructions       | Literal; assume nothing                                           |
| Pre-work           | `git commit` before any changes                                   |
| Steps              | Exact code/paths; show changes as git diff format                 |
| Verification       | `./checkpython.sh` clean, all tests pass, `ruff` + `mypy` clean  |
| Post-work          | `git commit` after verification passes                            |

**Campaign priority:** (1) Application Stability -- fix `pytest` blockers -> (2) Type Safety -- zero `mypy --strict` errors -> (3) Code Quality -- zero `ruff` errors

---

## PART 7: PYTHON 3.12 FEATURES REFERENCE

Full details with 3.11 fallbacks: `references/python-best-practices.md §23`.

| Feature                          | 3.12 Syntax                              | Min  |
| -------------------------------- | ---------------------------------------- | ---- |
| Type alias (PEP 695)             | `type Point = tuple[float, float]`       | 3.12 |
| Generic class                    | `class Stack[T]:`                        | 3.12 |
| Generic function                 | `def first[T](lst: list[T]) -> T:`      | 3.12 |
| `@override`                      | `from typing import override`            | 3.12 |
| F-string nested same-quotes      | `f"result: {', '.join(items)}"`          | 3.12 |
| `itertools.batched(it, n)`       | Yield size-n tuples                      | 3.12 |
| `pathlib.Path.walk()`            | `os.walk()` returning `Path` objects     | 3.12 |
| `sys.monitoring`                 | Low-overhead debugger/profiler API       | 3.12 |
| `tomllib`                        | TOML parsing (stdlib)                    | 3.11 |
| `except*`                        | Exception groups                         | 3.11 |
| `Self` type                      | `from typing import Self`                | 3.11 |
| `dataclass(slots=True)`          | Memory-efficient dataclasses             | 3.10 |
| `datetime.UTC`                   | Use instead of `timezone.utc`            | 3.11 |
| `match-case`                     | Structural pattern matching              | 3.10 |
| `contextlib.chdir`               | Context manager for directory changes    | 3.11 |
