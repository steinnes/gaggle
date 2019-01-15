setup:
	poetry install

test:
	poetry run pytest -s --cov-report term-missing --cov=gaggle tests/
