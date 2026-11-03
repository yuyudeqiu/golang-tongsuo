# Go + Tongsuo builder image

[简体中文](https://github.com/yuyudeqiu/golang-tongsuo/blob/main/README.zh-CN.md) | English

A reproducible, multi-platform Go build image with a statically built Tongsuo toolchain.

## Included versions

| Component | Version |
| --- | --- |
| Go base image | `golang:1.27.3-bookworm` |
| Tongsuo commit | `1206e6b7c0e13a7813b03e30b136202afd494f50` |
| Tongsuo archive SHA-256 | `3026cfbba8f3bcb1add69424530f533bec2ca41d5926842bd653c78745f41e17` |
| Platforms | `linux/amd64`, `linux/arm64` |

Tongsuo is installed under `/opt/tongsuo` with:

```text
enable-ntls enable-export-sm4 no-shared no-dso no-async
```

The image preconfigures `CGO_ENABLED`, `CGO_CFLAGS`, and `CGO_LDFLAGS` for Go builds.

## Image tags

Release tags use the format `<full Go version>-<short Tongsuo commit ID>`. For example, `1.27.3-1206e6b` contains Go `1.27.3` and Tongsuo commit `1206e6b7c0e13a7813b03e30b136202afd494f50`.

After a successful release, floating tags are synchronized from complete multi-platform images already published in this repository:

- `latest` follows the highest published stable Go version.
- Series tags such as `1.26` and `1.27` follow the highest published patch version within that series.
- If multiple releases contain the same Go version, the most recently published release is selected.

For example, publishing Go `1.26.11` after `1.27.3` updates `1.26` while `latest` stays on `1.27.3`. Use the full release tag for reproducible builds. Floating tags update in a separate workflow after the version image is published.

## Use the image

```dockerfile
FROM yuyudeqiu/golang-tongsuo:1.27.3-1206e6b AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -trimpath -o /out/app ./cmd/server
```

Because this image enables CGO, the resulting Go binary may still depend on the system C library even though Tongsuo itself is linked from static libraries. Check the application binary before selecting a minimal runtime image:

```bash
ldd /out/app
```

## Build locally

Build for the current machine:

```bash
docker build -t golang-tongsuo:local .
docker run --rm golang-tongsuo:local openssl version
```

Build both supported platforms without publishing:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag golang-tongsuo:local \
  .
```

## Upstream licenses

This image redistributes components from the official Go image and the Tongsuo project. Review and retain the license notices required by those upstream projects when publishing or redistributing the image.
