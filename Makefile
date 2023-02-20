init:
	pip install -r requirements_dev.txt

doc:
	# sphinx-apidoc --module-first -f -o docs/source pandas_xyz
	rm -f docs/source/reference/api/*.rst
	make -C docs/ clean
	make -C docs/ html

test:
	python -m unittest discover -p 'test*.py' -v

clean:
	rm -Rf *.egg-info build dist

testpublish:
	# git push origin && git push --tags origin
	$(MAKE) clean
	# pip install --quiet twine wheel
	# pip install twine wheel
	# python setup.py bdist_wheel
	python setup.py sdist bdist_wheel
	twine check dist/*
	twine upload -r testpypi dist/*
	# $(MAKE) clean

publish:
	# git push origin && git push --tags origin
	$(MAKE) clean
	# pip install --quiet twine wheel
	pip install twine wheel
	python setup.py sdist bdist_wheel
	twine check dist/*
	twine upload dist/*
	# $(MAKE) clean