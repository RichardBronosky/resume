import os
import sys
import pytest

# Add the package root directory to Python path
package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, package_root)

def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless explicitly requested."""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    """Add the integration option."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    ) 