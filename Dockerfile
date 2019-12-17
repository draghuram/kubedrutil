FROM alpine:3.8 AS runtime

# Install restic runtime dependencies and upgrade existing packages.
RUN apk update \
 && apk upgrade \
 && apk add --no-cache \
        ca-certificates \
        fuse \
        openssh \
        jq \
        musl \
        curl \
        tar \
        bzip2 \
        etcd \
        restic \
 && update-ca-certificates \
 && rm -rf /var/cache/apk/*

# Download kubectl
RUN curl -L -o /usr/local/bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.17.0/bin/linux/amd64/kubectl

COPY kubedrutil.sh /usr/local/bin

# ENTRYPOINT ["/usr/local/bin/restic"]
