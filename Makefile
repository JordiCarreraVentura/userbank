PY=bin/python

# Load credentials from .env (silently skips if missing)
-include .env

env:
	virtualenv -p 3.10 .

destroy:
	rm -fr bin
	rm -fr etc
	rm -fr lib
	rm -fr share
	rm -fr pyvenv.cfg

install:
	$(PY) -m pip install -r requirements.txt

build:
	$(PY) -m build

publish: build
	TWINE_USERNAME="$(PYPI_USERNAME)" TWINE_PASSWORD="$(PYPI_PASSWORD)" \
		$(PY) -m twine upload --repository pypi dist/*

publish-test: build
	TWINE_USERNAME="$(PYPI_USERNAME)" TWINE_PASSWORD="$(PYPI_PASSWORD)" \
		$(PY) -m twine upload --repository testpypi dist/*

all: destroy env install build