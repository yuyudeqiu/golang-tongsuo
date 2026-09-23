# syntax=docker/dockerfile:1.7

ARG GO_VERSION=1.26.8
FROM golang:${GO_VERSION}-bookworm

ARG TONGSUO_COMMIT=1206e6b7c0e13a7813b03e30b136202afd494f50
ARG TONGSUO_SHA256=3026cfbba8f3bcb1add69424530f533bec2ca41d5926842bd653c78745f41e17

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        libtext-template-perl \
        perl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
        "https://github.com/Tongsuo-Project/Tongsuo/archive/${TONGSUO_COMMIT}.tar.gz" \
        -o /tmp/tongsuo.tar.gz \
    && echo "${TONGSUO_SHA256}  /tmp/tongsuo.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/tongsuo.tar.gz -C /tmp \
    && cd "/tmp/Tongsuo-${TONGSUO_COMMIT}" \
    && ./config \
        --prefix=/opt/tongsuo \
        --libdir=lib \
        enable-ntls \
        enable-export-sm4 \
        no-shared \
        no-dso \
        no-async \
    && make -s -j"$(nproc)" \
    && make -s install_sw \
    && /opt/tongsuo/bin/openssl version \
    && test -f /opt/tongsuo/lib/libcrypto.a \
    && test -f /opt/tongsuo/lib/libssl.a \
    && rm -rf \
        /tmp/tongsuo.tar.gz \
        "/tmp/Tongsuo-${TONGSUO_COMMIT}"

ENV TONGSUO_HOME=/opt/tongsuo \
    PATH=/opt/tongsuo/bin:${PATH} \
    CGO_ENABLED=1 \
    CGO_CFLAGS="-I/opt/tongsuo/include -Wno-deprecated-declarations" \
    CGO_LDFLAGS="-L/opt/tongsuo/lib"

WORKDIR /src
