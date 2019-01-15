setup:
	poetry install

test:
	poetry run pytest -s --cov-report term-missing --cov=gaggle tests/


test_%:
	poetry run pytest -vsx tests -k $@ --pdb

lint:
	poetry run flake8 gaggle/ tests/
