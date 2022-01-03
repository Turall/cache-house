lint:
	@echo
	isort --diff -c --skip-glob '*.venv' .
	@echo
	flake8 .
	@echo
	mypy --ignore-missing-imports .


format_code:
	isort .



check: lint 