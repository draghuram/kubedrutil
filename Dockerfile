FROM alpine:3.10.3 AS runtime

# Install restic runtime dependencies and upgrade existing packages.
RUN apk update \
 && apk upgrade \
 && apk add --no-cache \
        ca-certificates \
        fuse \
        openssh \
        jq \
        curl \
        tar \
        bzip2 \
        etcd=3.4.3-r2 \
        restic=0.9.6-r0 \
 && update-ca-certificates \
 && rm -rf /var/cache/apk/*

# Download kubectl
RUN curl -L -o /usr/local/bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.17.0/bin/linux/amd64/kubectl

COPY kubedrutil.sh /usr/local/bin

# ENTRYPOINT ["/usr/local/bin/restic"]
