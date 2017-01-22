all: README.rst
	rm dist/* -f
	python setup.py bdist_wheel sdist

README.rst: README.md
	pandoc -f markdown -t rst $< > $@
pypi:
	twine upload dist/*
