# syntax=docker/dockerfile:1

FROM golang:1.22-alpine AS build

WORKDIR /src

COPY backend/go.mod backend/go.sum* ./
RUN go mod download || true

COPY backend /src
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/server ./cmd/server

FROM alpine:3.20

RUN apk add --no-cache ca-certificates

COPY --from=build /out/server /usr/local/bin/server
COPY backend/assets /assets
ENV IC_MEMO_LOGO_PATH=/assets/alif-logo.png

EXPOSE 8080
CMD ["/usr/local/bin/server"]
