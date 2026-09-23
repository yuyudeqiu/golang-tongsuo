# Go + Tongsuo 构建镜像

简体中文 | [English](README.md)

一个可复现、支持多平台的 Go 构建镜像，内置静态编译的铜锁（Tongsuo）工具链。

## 内置版本

| 组件 | 版本 |
| --- | --- |
| Go 基础镜像 | `golang:1.25.14-bookworm` |
| Tongsuo 提交 | `1206e6b7c0e13a7813b03e30b136202afd494f50` |
| Tongsuo 源码包 SHA-256 | `3026cfbba8f3bcb1add69424530f533bec2ca41d5926842bd653c78745f41e17` |
| 支持平台 | `linux/amd64`、`linux/arm64` |

Tongsuo 安装在 `/opt/tongsuo`，使用以下编译选项：

```text
enable-ntls enable-export-sm4 no-shared no-dso no-async
```

镜像已经为 Go 构建预先配置了 `CGO_ENABLED`、`CGO_CFLAGS` 和 `CGO_LDFLAGS`。

## 镜像标签

发布标签采用 `<Go 完整版本>-<Tongsuo 短 commit ID>` 格式。例如，`1.25.14-1206e6b` 表示镜像包含 Go `1.25.14` 和 Tongsuo 提交 `1206e6b7c0e13a7813b03e30b136202afd494f50`。

本项目不发布 `latest` 标签。请使用明确的版本标签，以保证构建可复现。

## 使用镜像

```dockerfile
FROM yuyudeqiu/golang-tongsuo:1.25.14-1206e6b AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -trimpath -o /out/app ./cmd/server
```

由于该镜像启用了 CGO，即使 Tongsuo 本身通过静态库链接，生成的 Go 二进制文件仍可能依赖系统 C 库。选择精简的运行时镜像前，请先检查应用程序二进制文件：

```bash
ldd /out/app
```

## 本地构建

为当前机器构建：

```bash
docker build -t golang-tongsuo:local .
docker run --rm golang-tongsuo:local openssl version
```

同时构建两个受支持的平台，但不发布镜像：

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag golang-tongsuo:local \
  .
```

## 上游许可证

该镜像重新分发了 Go 官方镜像和 Tongsuo 项目的组件。发布或重新分发该镜像时，请检查并保留这些上游项目要求的许可证声明。
