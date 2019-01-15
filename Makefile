setup:
	poetry install

test:
	poetry run pytest -s --cov-report term-missing --cov=gaggle tests/

lint:
	poetry run flake8 gaggle/ tests/
