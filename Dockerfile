ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install build dependencies for cryptography on Alpine
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Bypass s6-overlay entirely — run.sh becomes PID 1
COPY run.sh /
RUN chmod +x /run.sh

ENTRYPOINT []
CMD [ "/run.sh" ]
