run:
	FLASK_ENV=development python3 -m webclient --authentication-method developer --developer-username developer --api-url "http://127.0.0.1:8080" --frontend-url "http://127.0.0.1:5000" run

flake8:
	python3 -m flake8
