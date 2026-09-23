# Repository instructions

## Source of truth

- `Dockerfile` is the source of truth for `GO_VERSION`, `TONGSUO_COMMIT`, and `TONGSUO_SHA256`.
- Keep `README.md` and `README.zh-CN.md` synchronized when pinned versions, supported platforms, image usage, or user-visible behavior changes.
- Keep the README files focused on image users. Put repository maintenance and release procedures in this file instead of expanding the README files.
- `README.md` is also the source for the Docker Hub repository overview. Pushing a change to it on `main` triggers `.github/workflows/dockerhub-description.yml`.
- Keep links in `README.md` usable from both GitHub and Docker Hub. Prefer absolute URLs for links to other repository files.

## Updating Go or Tongsuo

1. Update the relevant build arguments at the top of `Dockerfile`.
2. When changing `TONGSUO_COMMIT`, download the archive for that exact full commit and update `TONGSUO_SHA256` to its verified SHA-256 digest.
3. Update the version tables and tag examples in both README files.
4. Build the image locally and verify that `/opt/tongsuo/bin/openssl version` runs and that `/opt/tongsuo/lib/libcrypto.a` and `/opt/tongsuo/lib/libssl.a` exist.
5. Do not suppress or bypass the archive checksum verification.

## Release tags

- Release tags use `<full Go version>-<short Tongsuo commit ID>`.
- The part before the hyphen must exactly match `GO_VERSION` in `Dockerfile`.
- The part after the hyphen must be the first seven characters of the full `TONGSUO_COMMIT` in `Dockerfile`.
- Example: `GO_VERSION=1.26.8` and `TONGSUO_COMMIT=1206e6b7c0e13a7813b03e30b136202afd494f50` produce `1.26.8-1206e6b`.
- Never reuse or move an existing release tag. Create a new tag whenever Go or the Tongsuo commit changes.
- Do not change only the checksum for an already published Go/Tongsuo combination. Investigate an unexpected archive checksum change and pin a new trusted Tongsuo commit before releasing.
- Tags matching `*.*.*-*` trigger `.github/workflows/docker.yml`; ordinary branch pushes do not publish an image.
- Do not create or push a release tag unless the user explicitly requests the release.

When a release is requested, verify the tag against `Dockerfile`, confirm the local build succeeds, then create and push it:

```bash
git tag <full Go version>-<short Tongsuo commit ID>
git push origin <full Go version>-<short Tongsuo commit ID>
```
