# Science
import pytest
import os

def pytest_addoption(parser):
    parser.addoption(
        "--datadir",
        action="store",
        default=None,
        help="Directory to store test data"
    )

@pytest.fixture(scope="session")
def datadir(request):
    user_dir = request.config.getoption("--datadir")
    if user_dir:
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    # fallback: use a default location in the repo or a temp dir
    #default = os.path.abspath("test_data_cache")
    #os.makedirs(default, exist_ok=True)
    return None