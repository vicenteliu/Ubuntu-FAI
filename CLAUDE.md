### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn’t listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Always execute all build and test commands inside the Docker container** to ensure a consistent environment. Use the `run.sh` script in the project root as the entry point.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility. The structure for this project is:
  - `build.py` - The main orchestrator script, responsible for reading the configuration, generating files, and invoking FAI.
  - `src/templates/` - Contains all Jinja2 templates, such as `user-data.yaml.j2` and `first-boot.service.j2`.
  - `fai_config_base/` - Contains the base, relatively static FAI Class and Hook scripts.
  - `first_boot_scripts/` - Contains scripts that will run on the first boot of the newly installed target system.
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use `python-dotenv` and `load_dotenv()`** to manage environment variables (if needed, e.g., for API keys).

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features**, especially for core logic functions within `build.py`.
- **After updating any logic, check whether existing unit tests need to be updated.** If so, do it.
- **Tests should live in a `/tests` folder**, mirroring the main app structure.
- Tests should include at least:
  - Tests for the `config.json` parsing and validation logic.
  - Tests for the Jinja2 template rendering that generates `user-data.yaml`.
  - 1 test for the expected success case.
  - 1 edge case test (e.g., optional fields in `config.json` are missing).
  - 1 failure case test (e.g., malformed `config.json` or missing required fields).

### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- **Add any new sub-tasks or TODOs** discovered during development to `TASK.md` under a “Discovered During Work” section.

### 📎 Style & Conventions
- **Use Python** as the primary programming language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for reading and validating `config.json` data** to ensure configuration robustness.
- **Core Libraries**: `requests` (for downloading), `Jinja2` (for template rendering), `PyYAML` (for handling YAML files).
- **Write Google-style docstrings for every function**:
  ```python
  def example_function(param1: str) -> bool:
      """A brief, one-line summary.

      Args:
          param1 (str): A description of the parameter.

      Returns:
          bool: A description of the return value.
      """