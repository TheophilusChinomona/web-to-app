import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Update golden snapshot files",
    )


@pytest.fixture
def update_goldens(request):
    return bool(request.config.getoption("--update-goldens"))
