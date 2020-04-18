FROM python:3.8-slim

ARG BUILD_DATE=""
ARG BUILD_VERSION="dev"

LABEL maintainer="truebrain@openttd.org"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.build-date=${BUILD_DATE}
LABEL org.label-schema.version=${BUILD_VERSION}

WORKDIR /code

COPY requirements.txt \
        LICENSE \
        README.md \
        .version \
        /code/
# Needed for Sentry to know what version we are running
RUN echo "${BUILD_VERSION}" > /code/.version

RUN pip --no-cache-dir install -r requirements.txt

# Validate that what was installed was what was expected
RUN pip freeze 2>/dev/null > requirements.installed \
    && diff -u --strip-trailing-cr requirements.txt requirements.installed 1>&2 \
    || ( echo "!! ERROR !! requirements.txt defined different packages or versions for installation" \
        && exit 1 ) 1>&2

COPY webclient /code/webclient

ENTRYPOINT ["python", "-m", "webclient"]
CMD ["--authentication-method", "developer", "--developer-username", "developer", "--api-url", "http://127.0.0.1:8080", "--frontend-url", "https://127.0.0.1:5000", "run", "-p", "80", "-h", "0.0.0.0"]
