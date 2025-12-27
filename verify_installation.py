"""
Verification script for dependency installation.
Tests importing all key packages to ensure successful installation.
"""
import sys

def verify_imports():
    """Test importing all required packages and report versions."""
    results = []
    errors = []

    packages = [
        ("streamlit", "Streamlit UI Framework"),
        ("pydantic_ai", "PydanticAI Agent Framework"),
        ("dotenv", "Python Dotenv"),
        ("openai", "OpenAI SDK"),
        ("yfinance", "YFinance Financial Data"),
        ("tavily", "Tavily Research API"),
        ("logfire", "LogFire Observability"),
        ("pytest", "Pytest Testing Framework"),
        ("black", "Black Code Formatter"),
        ("flake8", "Flake8 Linter"),
        ("mypy", "MyPy Type Checker"),
        ("requests", "Requests HTTP Library"),
    ]

    print("=" * 60)
    print("DEPENDENCY INSTALLATION VERIFICATION")
    print("=" * 60)
    print()

    for package_name, description in packages:
        try:
            module = __import__(package_name)
            version = getattr(module, "__version__", "version unavailable")
            results.append(f"[OK] {description:35s} {version}")
        except ImportError as e:
            errors.append(f"[FAIL] {description:35s} ImportError: {e}")

    # Print results
    for result in results:
        print(result)

    if errors:
        print()
        print("ERRORS DETECTED:")
        for error in errors:
            print(error)
        return False
    else:
        print()
        print("=" * 60)
        print("ALL PACKAGES INSTALLED SUCCESSFULLY")
        print("=" * 60)
        return True

if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
