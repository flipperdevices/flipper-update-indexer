VERSION := 0.0.0

.PHONY: run
run: venv requirements
	./venv/bin/python3 indexer/main.py

venv:
	python3 -m venv venv

.PHONY: requirements
requirements: venv
	./venv/bin/pip install -q -r indexer/requirements.txt

.PHONY: clean
clean:
	rm -rf venv

.PHONY: lint
lint: venv requirements
	./venv/bin/black . --check

.PHONY: format
format: venv requirements
	./venv/bin/black .
