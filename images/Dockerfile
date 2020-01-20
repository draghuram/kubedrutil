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
        python3 \
 && update-ca-certificates \
 && rm -rf /var/cache/apk/*

# Download etcd
RUN curl -L https://github.com/etcd-io/etcd/releases/download/v3.3.18/etcd-v3.3.18-linux-amd64.tar.gz | tar -xzv \
        && mv etcd*/etcdctl /usr/local/bin/etcdctl \
        && rm -rf ./etcd

# Download restic
RUN curl -L -o ./restic.bz2 https://github.com/restic/restic/releases/download/v0.9.6/restic_0.9.6_linux_amd64.bz2 \
        && bzip2 -d ./restic*.bz2 \
        && mv ./restic* /usr/local/bin/restic \
        && chmod +x /usr/local/bin/restic

# Download kubectl
RUN curl -L -o /usr/local/bin/kubectl \
    https://storage.googleapis.com/kubernetes-release/release/v1.17.0/bin/linux/amd64/kubectl \
    && chmod +x /usr/local/bin/kubectl


COPY kubedrutil.sh /usr/local/bin
COPY kubedrutil /opt/kubedrutil

RUN python3 -m venv /opt/venv/kubedrutil \
     && /opt/venv/kubedrutil/bin/pip install /opt/kubedrutil \
     && ln -s /opt/venv/kubedrutil/bin/kubedrutil /usr/local/bin/kubedrutil

# ENTRYPOINT ["/usr/local/bin/restic"]
