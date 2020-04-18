.PHONY: run venv flake8

run: .env/pyvenv.cfg
	FLASK_ENV=development .env/bin/python3 -m webclient --authentication-method developer --developer-username developer --api-url "http://127.0.0.1:8080" --tus-url "http://127.0.0.1:1080" --frontend-url "https://127.0.0.1:5000" run

venv: .env/pyvenv.cfg

.env/pyvenv.cfg: requirements.txt
	python3 -m venv .env
	.env/bin/pip install -r requirements.txt

flake8:
	python3 -m flake8 webclient
