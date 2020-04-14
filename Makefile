run:
	FLASK_APP=webclient python3 -m flask run

debug:
	FLASK_APP=webclient FLASK_ENV=development python3 -m flask run

flake8:
	python3 -m flake8
