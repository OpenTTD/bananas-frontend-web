.PHONY: run venv flake8

run: .env/pyvenv.cfg
	FLASK_ENV=development .env/bin/python3 -m webclient --authentication-method developer --api-url "http://localhost:8080" --tus-url "http://localhost:1080" --frontend-url "http://localhost:5000" --client-id developer run

venv: .env/pyvenv.cfg

.env/pyvenv.cfg: requirements.txt
	python3 -m venv .env
	.env/bin/pip install -r requirements.txt

flake8:
	python3 -m flake8 webclient
