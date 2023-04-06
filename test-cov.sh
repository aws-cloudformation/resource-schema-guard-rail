pytest --cov="src" --cov-report=term-missing tests/unit --pyargs --verbose -vv
coverage html
open htmlcov/index.html