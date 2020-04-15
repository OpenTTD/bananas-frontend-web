# BaNaNaS web front-end

This is a front-end for browsing and upload content to OpenTTD's content service, called BaNaNaS.
It works together with [bananas-api](https://github.com/OpenTTD/bananas-api), which serves the HTTP API.

## Development

This front-end is written in Python 3.7 with Flask.

## Usage

To start it, you are advised to first create a virtualenv:

```bash
python3 -m venv .env
.env/bin/pip install -r requirements.txt
```

After this, you can run the flask application by running:

```bash
make run
```
