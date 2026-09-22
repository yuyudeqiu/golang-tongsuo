# Go + Tongsuo builder image

A reproducible, multi-platform Go build image with a statically built Tongsuo toolchain.

## Included versions

| Component | Version |
| --- | --- |
| Go base image | `golang:1.25.14-bookworm` |
| Tongsuo commit | `1206e6b7c0e13a7813b03e30b136202afd494f50` |
| Tongsuo archive SHA-256 | `3026cfbba8f3bcb1add69424530f533bec2ca41d5926842bd653c78745f41e17` |
| Platforms | `linux/amd64`, `linux/arm64` |

Tongsuo is installed under `/opt/tongsuo` with:

```text
enable-ntls enable-export-sm4 no-shared no-dso no-async
```

The image preconfigures `CGO_ENABLED`, `CGO_CFLAGS`, and `CGO_LDFLAGS` for Go builds.

## Use the image

Replace `YOUR_DOCKERHUB_USERNAME` with the Docker Hub namespace that publishes the image:

```dockerfile
FROM YOUR_DOCKERHUB_USERNAME/golang-tongsuo:1.25.14-1206e6b AS builder

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

## Publish with GitHub Actions

1. Create a public Docker Hub repository named `golang-tongsuo`.
2. Create a Docker Hub access token with read/write permission.
3. Add the GitHub Actions repository variable `DOCKERHUB_USERNAME`.
4. Add the GitHub Actions repository secret `DOCKERHUB_TOKEN`.

5. Push a version tag to trigger the build and publish a Docker image with the same tag:

```bash
git tag 1.25.14-1206e6b
git push origin 1.25.14-1206e6b
```

Docker Hub then serves one tag with architecture-specific images. A normal `docker pull` automatically selects `linux/amd64` or `linux/arm64` for the host.

Normal pushes to `main` do not publish an image. Only tags matching `*.*.*-*`, such as `1.25.14-1206e6b`, trigger this workflow. The first part is the Go version and the suffix is the short Tongsuo commit ID.

## Updating versions

When changing Go or Tongsuo, update the three build arguments at the top of the `Dockerfile`, verify the downloaded archive checksum, build locally, and publish a new version tag. Do not reuse an existing version tag for different contents.

## Upstream licenses

This image redistributes components from the official Go image and the Tongsuo project. Review and retain the license notices required by those upstream projects when publishing or redistributing the image.
