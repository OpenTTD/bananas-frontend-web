# BaNaNaS web front-end

[![GitHub License](https://img.shields.io/github/license/OpenTTD/bananas-frontend-web)](https://github.com/OpenTTD/bananas-frontend-web/blob/main/LICENSE)

This is a front-end for browsing and upload content to OpenTTD's content service, called BaNaNaS.
It works together with [bananas-api](https://github.com/OpenTTD/bananas-api), which serves the HTTP API.

See [introduction.md](https://github.com/OpenTTD/bananas-api/tree/main/docs/introduction.md) for more documentation about the different BaNaNaS components and how they work together.

## Development

This front-end is written in Python 3.7 with Flask.

## Usage

To start it, you are advised to first create a virtualenv:

```bash
npm install
python3 -m venv .env
.env/bin/pip install -r requirements.txt
```

After this, you can run the flask application by running:

```bash
make run
```

### Running via docker

```bash
docker build -t openttd/bananas-frontend-web:local .
docker run --rm -p 127.0.0.1:5000:80 openttd/bananas-frontend-web:local
```
