#!/bin/zsh
# Enhanced Python Quality Check Script with Command Line Options
# This script runs static analysis and formatting checks with configurable options
#
# USAGE:
#   ./checkpython.sh [OPTIONS]
#
# OPTIONS:
#   --exclude TEST        Exclude a specific test (can be used multiple times)
#                         Valid tests: autopep8, ruff, mypy, refurb, vulture, deptry, radon, cohesion, bandit, pytest, grimp, great_expectations, pyright, cosmic-ray
#   --only TEST           Run only the specified test, skip all others
#   --include-tests-dir   Include the tests/ directory in analysis (by default it's excluded if present)
#   --help, -h            Show help message with usage examples
#
# EXAMPLES:
#   ./checkpython.sh                            # Run all tests (auto-excludes tests/ dir if present)
#   ./checkpython.sh --exclude bandit           # Run all tests except bandit
#   ./checkpython.sh --exclude ruff --exclude mypy # Exclude multiple tests
#   ./checkpython.sh --only pytest              # Run only pytest
#   ./checkpython.sh --include-tests-dir        # Include tests/ directory in all analysis
#
# AUTOMATIC BEHAVIOR:
#   - If a tests/ directory exists, it will be automatically excluded from analysis tools
#   - This prevents test code from affecting quality metrics for production code
#   - Use --include-tests-dir to override this behavior

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure docs/reports directory exists for outputs
mkdir -p docs/reports

# Default settings - all tests enabled by default (some exceptions below)
# These variables control which tests are run (1=enabled, 0=disabled)
RUN_AUTOPEP8=1
RUN_RUFF=1
RUN_SEMGREP=1
RUN_MYPY=1
RUN_REFURB=1
RUN_VULTURE=0
RUN_DEPTRY=1
RUN_RADON=1
RUN_COHESION=1 # Cohesion is off by default (can be slow)
RUN_BANDIT=0 # Bandit is off by default
RUN_PYTEST=1
RUN_GRIMP=1
RUN_GREAT_EXPECTATIONS=0 # Enabled as user installed it
RUN_PYRIGHT=1
RUN_COSMIC_RAY=0 # Enabled as user installed it

# Test directory exclusion flag
# When set to 1, the tests/ directory will be excluded from analysis tools
# This prevents test code from affecting quality metrics for production code
EXCLUDE_TESTS_DIR=0

# Auto-detect if tests directory exists and set exclusion flag
# This provides sensible defaults - test code is excluded from quality checks
[ -d "tests" ] && EXCLUDE_TESTS_DIR=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --exclude)
            shift
            case $1 in
                autopep8) RUN_AUTOPEP8=0 ;;
                ruff) RUN_RUFF=0 ;;
                semgrep) RUN_SEMGREP=0 ;;
                mypy) RUN_MYPY=0 ;;
                refurb) RUN_REFURB=0 ;;
                vulture) RUN_VULTURE=0 ;;
                deptry) RUN_DEPTRY=0 ;;
                radon) RUN_RADON=0 ;;
                cohesion) RUN_COHESION=0 ;;
                bandit) RUN_BANDIT=0 ;;
                pytest) RUN_PYTEST=0 ;;
                grimp) RUN_GRIMP=0 ;;
                great_expectations) RUN_GREAT_EXPECTATIONS=0 ;;
                pyright) RUN_PYRIGHT=0 ;;
                cosmic-ray) RUN_COSMIC_RAY=0 ;;
                *)
                    echo "Unknown test to exclude: $1"
                    echo "Valid options: autopep8, ruff, semgrep, mypy, refurb, vulture, deptry, radon, cohesion, bandit, pytest, grimp, great_expectations, pyright, cosmic-ray"
                    exit 1
                    ;;
            esac
            shift
            ;;
        --only)
            # First disable all tests
            RUN_AUTOPEP8=0
            RUN_RUFF=0
            RUN_SEMGREP=0
            RUN_MYPY=0
            RUN_REFURB=0
            RUN_VULTURE=0
            RUN_DEPTRY=0
            RUN_RADON=0
            RUN_COHESION=0
            RUN_BANDIT=0
            RUN_PYTEST=0
            RUN_GRIMP=0
            RUN_GREAT_EXPECTATIONS=0
            RUN_PYRIGHT=0
            RUN_COSMIC_RAY=0

            shift
            case $1 in
                autopep8) RUN_AUTOPEP8=1 ;;
                ruff) RUN_RUFF=1 ;;
                semgrep) RUN_SEMGREP=1 ;;
                mypy) RUN_MYPY=1 ;;
                refurb) RUN_REFURB=1 ;;
                vulture) RUN_VULTURE=1 ;;
                deptry) RUN_DEPTRY=1 ;;
                radon) RUN_RADON=1 ;;
                cohesion) RUN_COHESION=1 ;;
                bandit) RUN_BANDIT=1 ;;
                pytest) RUN_PYTEST=1 ;;
                grimp) RUN_GRIMP=1 ;;
                great_expectations) RUN_GREAT_EXPECTATIONS=1 ;;
                pyright) RUN_PYRIGHT=1 ;;
                cosmic-ray) RUN_COSMIC_RAY=1 ;;
                *)
                    echo "Unknown test: $1"
                    echo "Valid options: autopep8, ruff, semgrep, mypy, refurb, vulture, deptry, radon, cohesion, bandit, pytest, grimp, great_expectations, pyright, cosmic-ray"
                    exit 1
                    ;;
            esac
            shift
            ;;
        --include-tests-dir)
            EXCLUDE_TESTS_DIR=0
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --exclude TEST        Exclude a specific test (can be used multiple times)"
            echo "                        Valid tests: autopep8, ruff, semgrep, mypy, refurb, vulture, deptry, radon, cohesion, bandit, pytest, grimp, great_expectations, pyright, cosmic-ray"
            echo "  --only TEST           Run only the specified test"
            echo "  --include-tests-dir   Include tests/ directory in analysis (overrides auto-exclusion)"
            echo "  --help, -h            Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2 passed${NC}"
    else
        echo -e "${RED}❌ $2 failed${NC}"
        return 1
    fi
}

# Timestamp for reports
TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)

# Track overall success
OVERALL_SUCCESS=0

# Display configuration
echo "🔧 Configuration:"
echo "  Running autopep8: $([ $RUN_AUTOPEP8 -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running ruff: $([ $RUN_RUFF -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running semgrep: $([ $RUN_SEMGREP -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running mypy: $([ $RUN_MYPY -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running refurb: $([ $RUN_REFURB -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running vulture: $([ $RUN_VULTURE -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
echo "  Running deptry: $([ $RUN_DEPTRY -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running radon: $([ $RUN_RADON -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running cohesion: $([ $RUN_COHESION -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
echo "  Running bandit: $([ $RUN_BANDIT -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
echo "  Running pytest: $([ $RUN_PYTEST -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
echo "  Running grimp: $([ $RUN_GRIMP -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running great_expectations: $([ $RUN_GREAT_EXPECTATIONS -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
echo "  Running pyright: $([ $RUN_PYRIGHT -eq 1 ] && echo "YES" || echo "NO")"
echo "  Running cosmic-ray: $([ $RUN_COSMIC_RAY -eq 1 ] && echo "YES" || echo "NO (disabled by default)")"
if [ -d "tests" ]; then
    echo "  Excluding tests/: $([ $EXCLUDE_TESTS_DIR -eq 1 ] && echo "YES (use --include-tests-dir to override)" || echo "NO")"
fi
echo ""

# Initial cleaning
echo "Beginning cleaning."
pyclean .

# ===== CODE FORMATTING AND LINTING SECTION =====

# Run autopep8 if enabled
if [ $RUN_AUTOPEP8 -eq 1 ]; then
    echo "Beginning autopep8."
    if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
        find . -path './.*' -prune -o -path './tests' -prune -o -name "*.py" -print -exec autopep8 --in-place --max-line-length 88 {} +
    else
        find . -path './.*' -prune -o -name "*.py" -exec autopep8 --in-place --max-line-length 88 {} +
    fi
fi

# Run ruff if enabled
if [ $RUN_RUFF -eq 1 ]; then
    echo "Beginning ruff."
    REPORT_FILE="docs/reports/ruff-${TIMESTAMP}.txt"
    if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
        ruff check . --fix --exclude="tests/" > "$REPORT_FILE" 2>&1
        ruff format --exclude="tests/" >> "$REPORT_FILE" 2>&1
    else
        ruff check . --fix > "$REPORT_FILE" 2>&1
        ruff format >> "$REPORT_FILE" 2>&1
    fi
    RUFF_EXIT=$?
    print_status $RUFF_EXIT "Ruff check and format" || OVERALL_SUCCESS=1
fi

# ===== ANTIPATTERN GUARDRAILS SECTION =====

# Run semgrep if enabled
if [ $RUN_SEMGREP -eq 1 ]; then
    echo "Beginning semgrep antipattern scan."
    REPORT_FILE="docs/reports/semgrep-${TIMESTAMP}.txt"
    if command -v semgrep &> /dev/null; then
        if [ -f ".semgrep/rules.yaml" ]; then
            if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
                semgrep --config .semgrep/rules.yaml . --exclude tests/ --exclude src/scripts/ > "$REPORT_FILE" 2>&1
            else
                semgrep --config .semgrep/rules.yaml . --exclude src/scripts/ > "$REPORT_FILE" 2>&1
            fi
            SEMGREP_EXIT=$?
            print_status $SEMGREP_EXIT "Semgrep antipattern scan" || true
        else
            echo -e "${YELLOW}⚠️  .semgrep/rules.yaml not found, skipping antipattern scan${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Semgrep not found, skipping antipattern scan${NC}"
    fi
fi
# ===== TYPE CHECKING SECTION =====

# Run mypy if enabled
if [ $RUN_MYPY -eq 1 ]; then
    echo "Beginning mypy."
    REPORT_FILE="docs/reports/mypy-${TIMESTAMP}.txt"
    if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
        mypy . --exclude 'tests/' > "$REPORT_FILE" 2>&1
    else
        mypy . > "$REPORT_FILE" 2>&1
    fi
    MYPY_EXIT=$?
    print_status $MYPY_EXIT "MyPy type checking" || OVERALL_SUCCESS=1
fi

# Run pyright if enabled (New Tool)
if [ $RUN_PYRIGHT -eq 1 ]; then
    echo "Beginning pyright."
    REPORT_FILE="docs/reports/pyright-${TIMESTAMP}.txt"
    if command -v pyright &> /dev/null; then
        pyright . > "$REPORT_FILE" 2>&1
        PYRIGHT_EXIT=$?
        print_status $PYRIGHT_EXIT "Pyright type checking" || OVERALL_SUCCESS=1
    else
        echo -e "${YELLOW}⚠️  Pyright not found, skipping${NC}"
    fi
fi

# ===== MODERNIZATION CHECK =====

# Run refurb if enabled
if [ $RUN_REFURB -eq 1 ]; then
    echo "Beginning refurb modernization check."
    REPORT_FILE="docs/reports/refurb-${TIMESTAMP}.txt"
    if command -v refurb &> /dev/null; then
        if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
            refurb src/ > "$REPORT_FILE" 2>&1
        else
            refurb . > "$REPORT_FILE" 2>&1
        fi
        REFURB_EXIT=$?
        # Refurb findings are advisory
        print_status $REFURB_EXIT "Refurb modernization" || true
    else
        echo -e "${YELLOW}⚠️  Refurb not found, skipping modernization check${NC}"
    fi
fi

# ===== DEPENDENCY ANALYSIS SECTION =====

# Run grimp if enabled (New Tool)
# Grimp builds a graph of imports within the package
if [ $RUN_GRIMP -eq 1 ]; then
    echo "Beginning grimp import analysis."
    REPORT_FILE="docs/reports/grimp-${TIMESTAMP}.txt"
    if python -c "import grimp" 2>/dev/null; then
        # Use Python wrapper script since grimp is a library, not a CLI tool
        python -m src.scripts.utility_grimp_analysis --output "$REPORT_FILE"
        GRIMP_EXIT=$?
        print_status $GRIMP_EXIT "Grimp import analysis" || true
    else
        echo -e "${YELLOW}⚠️  Grimp not found, skipping${NC}"
    fi
fi

# Run deptry if enabled
if [ $RUN_DEPTRY -eq 1 ]; then
    echo "Beginning deptry dependency check."
    REPORT_FILE="docs/reports/deptry-${TIMESTAMP}.txt"
    if command -v deptry &> /dev/null; then
        deptry . > "$REPORT_FILE" 2>&1
        DEPTRY_EXIT=$?
        # Deptry findings are advisory
        print_status $DEPTRY_EXIT "Deptry dependency check" || true
    else
        echo -e "${YELLOW}⚠️  Deptry not found, skipping dependency check${NC}"
    fi
fi

# ===== DEAD CODE ANALYSIS =====

# Run vulture if enabled
if [ $RUN_VULTURE -eq 1 ]; then
    echo "Beginning vulture dead code analysis."
    REPORT_FILE="docs/reports/vulture-${TIMESTAMP}.txt"
    if command -v vulture &> /dev/null; then
        if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
            vulture . --min-confidence 80 --exclude tests/ > "$REPORT_FILE" 2>&1
        else
            vulture . --min-confidence 80 > "$REPORT_FILE" 2>&1
        fi
        VULTURE_EXIT=$?
        print_status $VULTURE_EXIT "Vulture dead code analysis" || OVERALL_SUCCESS=1
    else
        echo -e "${YELLOW}⚠️  Vulture not found, skipping dead code analysis${NC}"
    fi
fi

# ===== CODE COMPLEXITY ANALYSIS =====

# Run radon complexity check if enabled
if [ $RUN_RADON -eq 1 ]; then
    echo "Beginning radon complexity check."
    REPORT_FILE="docs/reports/radon-${TIMESTAMP}.txt"
    if command -v radon &> /dev/null; then
        # Check cyclomatic complexity
        if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
            RADON_OUTPUT=$(radon cc . -s --exclude="tests/*")
        else
            RADON_OUTPUT=$(radon cc . -s)
        fi
        echo "$RADON_OUTPUT" > "$REPORT_FILE"
        RADON_EXIT=$?

        # Check for files with complexity C, D, E, or F
        BAD_COMPLEXITY=$(echo "$RADON_OUTPUT" | grep -E " - [C-F] " | wc -l || echo 0)

        if [ "$BAD_COMPLEXITY" -gt 0 ]; then
            echo -e "${RED}🛑 Found $BAD_COMPLEXITY functions with high complexity (C, D, E, or F)${NC}"
            echo -e "${YELLOW}Functions with complexity C, D, E, or F need refactoring (see $REPORT_FILE)${NC}"
            OVERALL_SUCCESS=1
            print_status 1 "Radon complexity check" || true
        else
            print_status 0 "Radon complexity check"
        fi
    else
        echo -e "${YELLOW}⚠️  Radon not found, skipping complexity check${NC}"
    fi
fi

# ===== GOD CLASS DETECTION =====

# Run cohesion if enabled
if [ $RUN_COHESION -eq 1 ]; then
    echo "Beginning cohesion analysis (LCOM4 God Class detection)."
    REPORT_FILE="docs/reports/cohesion-${TIMESTAMP}.txt"
    if command -v cohesion &> /dev/null; then
        if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
            cohesion --below=50 src/ > "$REPORT_FILE" 2>&1
        else
            cohesion --below=50 . > "$REPORT_FILE" 2>&1
        fi
        COHESION_EXIT=$?
        # Cohesion findings are advisory
        print_status $COHESION_EXIT "Cohesion analysis" || true
    else
        echo -e "${YELLOW}⚠️  Cohesion not found, skipping God Class detection${NC}"
    fi
fi

# ===== SECURITY ANALYSIS =====

# Run bandit security scan if enabled
if [ $RUN_BANDIT -eq 1 ]; then
    echo "Beginning bandit."
    REPORT_FILE="docs/reports/bandit-${TIMESTAMP}.json"
    if command -v bandit &> /dev/null; then
        if [ $EXCLUDE_TESTS_DIR -eq 1 ]; then
            bandit -r . --exclude tests/ -f json -o "$REPORT_FILE" 2>/dev/null || true
            bandit -r . --exclude tests/ --severity-level medium
        else
            bandit -r . -f json -o "$REPORT_FILE" 2>/dev/null || true
            bandit -r . --severity-level medium
        fi
        BANDIT_EXIT=$?
        print_status $BANDIT_EXIT "Bandit security scan" || OVERALL_SUCCESS=1
    else
        echo -e "${YELLOW}⚠️  Bandit not found, skipping security scan${NC}"
    fi
fi

# ===== TESTING SECTION =====

# Run pytest if enabled
if [ $RUN_PYTEST -eq 1 ]; then
    echo "Beginning pytest."
    REPORT_FILE="docs/reports/pytest-${TIMESTAMP}.txt"
    if command -v pytest &> /dev/null; then
        # Run tests with coverage if tests directory exists
        if [ -d "tests" ]; then
            pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:logs/coverage-html --cov-report=json:logs/coverage.json --junit-xml=logs/test-results.xml -v > "$REPORT_FILE" 2>&1
            PYTEST_EXIT=$?
            print_status $PYTEST_EXIT "Pytest testing" || OVERALL_SUCCESS=1

            # Check coverage threshold (80%)
            if [ -f "logs/coverage.json" ]; then
                COVERAGE=$(python -c "import json; data=json.load(open('logs/coverage.json')); print(int(data['totals']['percent_covered']))")
                if [ "$COVERAGE" -ge 80 ]; then
                    echo -e "${GREEN}✅ Coverage: ${COVERAGE}% (meets 80% threshold)${NC}"
                else
                    echo -e "${YELLOW}🟡 Coverage: ${COVERAGE}% (below 80% threshold)${NC}"
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  No tests directory found, skipping pytest${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Pytest not found, skipping testing${NC}"
    fi
fi

# ===== DATA QUALITY SECTION (NEW) =====

# Run great_expectations if enabled (New Tool)
if [ $RUN_GREAT_EXPECTATIONS -eq 1 ]; then
    echo "Beginning great_expectations."
    REPORT_FILE="docs/reports/great_expectations-${TIMESTAMP}.txt"
    if command -v great_expectations &> /dev/null; then
        # Assumes 'great_expectations checkpoint run' or similar is configured
        great_expectations --v > "$REPORT_FILE" 2>&1 # Placeholder command
        GX_EXIT=$?
        print_status $GX_EXIT "Great Expectations" || true
    else
        echo -e "${YELLOW}⚠️  Great Expectations not found, skipping${NC}"
    fi
fi

# ===== MUTATION TESTING SECTION (NEW) =====

# Run cosmic-ray if enabled (New Tool)
if [ $RUN_COSMIC_RAY -eq 1 ]; then
    echo "Beginning cosmic-ray (Mutation Testing)."
    REPORT_FILE="docs/reports/cosmic-ray-${TIMESTAMP}.txt"
    if command -v cosmic-ray &> /dev/null; then
        # Warning: This is very slow. Usually run on a subset or specific config.
        # This is a placeholder for the init/exec commands
        echo "Cosmic Ray is installed but requires specific configuration (init/exec)." > "$REPORT_FILE"
        print_status 0 "Cosmic Ray (Placeholder)" || true
    else
        echo -e "${YELLOW}⚠️  Cosmic Ray not found, skipping${NC}"
    fi
fi

# Additional quality checks
echo ""
echo "🔍 Additional quality checks..."

# Check for TODO/FIXME comments in source code
if [ -d "src" ]; then
    # Build find command based on exclusion settings
    if [ $EXCLUDE_TESTS_DIR -eq 1 ] && [ -d "tests" ]; then
        TODO_COUNT=$(find src/ -path './tests' -prune -o -name "*.py" -print | xargs grep -l "TODO\|FIXME\|XXX" 2>/dev/null | wc -l || echo 0)
    else
        TODO_COUNT=$(find src/ -name "*.py" -exec grep -l "TODO\|FIXME\|XXX" {} \; 2>/dev/null | wc -l || echo 0)
    fi

    if [ "$TODO_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}🟡 Found $TODO_COUNT files with TODO/FIXME comments${NC}"
        if [ $EXCLUDE_TESTS_DIR -eq 1 ] && [ -d "tests" ]; then
            find src/ -path './tests' -prune -o -name "*.py" -print | xargs grep -Hn "TODO\|FIXME\|XXX" 2>/dev/null || true
        else
            find src/ -name "*.py" -exec grep -Hn "TODO\|FIXME\|XXX" {} \; 2>/dev/null || true
        fi
    fi

    # Check for print statements in source code
    if [ $EXCLUDE_TESTS_DIR -eq 1 ] && [ -d "tests" ]; then
        PRINT_COUNT=$(find src/ -path './tests' -prune -o -name "*.py" -print | xargs grep -l "print(" 2>/dev/null | wc -l || echo 0)
    else
        PRINT_COUNT=$(find src/ -name "*.py" -exec grep -l "print(" {} \; 2>/dev/null | wc -l || echo 0)
    fi

    if [ "$PRINT_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}🟡 Found $PRINT_COUNT files with print() statements (consider using logging)${NC}"
    fi

    # Check for hardcoded secrets patterns
    SECRET_PATTERNS="password|secret|key|token|api_key"
    if [ $EXCLUDE_TESTS_DIR -eq 1 ] && [ -d "tests" ]; then
        SECRET_COUNT=$(find src/ -path './tests' -prune -o -name "*.py" -print | xargs grep -il "$SECRET_PATTERNS" 2>/dev/null | wc -l || echo 0)
    else
        SECRET_COUNT=$(find src/ -name "*.py" -exec grep -il "$SECRET_PATTERNS" {} \; 2>/dev/null | wc -l || echo 0)
    fi

    if [ "$SECRET_COUNT" -gt 0 ]; then
        echo -e "${RED}🛑 Found potential hardcoded secrets in $SECRET_COUNT files${NC}"
        if [ $EXCLUDE_TESTS_DIR -eq 1 ] && [ -d "tests" ]; then
            find src/ -path './tests' -prune -o -name "*.py" -print | xargs grep -Hin "$SECRET_PATTERNS" 2>/dev/null || true
        else
            find src/ -name "*.py" -exec grep -Hin "$SECRET_PATTERNS" {} \; 2>/dev/null || true
        fi
        OVERALL_SUCCESS=1
    fi
fi

# Final cleaning
echo ""
echo "Beginning final cleaning."
pyclean .

# Final status report
echo ""
echo "📊 Quality Check Summary"
echo "========================"

if [ $OVERALL_SUCCESS -eq 0 ]; then
    echo -e "${GREEN}🟢 All quality checks passed!${NC}"
    echo "✨ Code is ready for production"
    exit 0
else
    echo -e "${RED}🛑 Some quality checks failed${NC}"
    echo "🔧 Please fix the issues above before proceeding"
    exit 1
fi
