ARG PY_VERSION='3.11'
FROM python:${PY_VERSION} AS builder
WORKDIR /mnemo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:${PY_VERSION}
WORKDIR /mnemo

ARG PY_VERSION
COPY --from=builder /usr/local/lib/python${PY_VERSION} /usr/local/lib/python${PY_VERSION}
COPY --from=builder /mnemo /mnemo

ENV AUGER_SOURCE='https://github.com/etcd-io/auger/releases/download/v1.0.3/auger_1.0.3_linux_arm64.tar.gz'
RUN curl -L $AUGER_SOURCE | tar -xz && mv auger /usr/local/bin/

EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["main.py"]