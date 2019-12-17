FROM alpine:3.10.3 AS runtime

ENV ETCD_VERSION 3.3.18
ENV RESTIC_VERSION 0.9.6
ENV KUBECTL_VERSION 1.17.0

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
 && update-ca-certificates \
 && rm -rf /var/cache/apk/*

# Download etcd
RUN curl -L https://github.com/etcd-io/etcd/releases/download/v$ETCD_VERSION/etcd-v$ETCD_VERSION-linux-amd64.tar.gz | tar xzv \
       && mv etcd*/etcdctl /usr/local/bin/etcdctl \
       && rm -rf ./etcd

# Download restic
RUN curl -L -o ./restiz.bz2 https://github.com/restic/restic/releases/download/v$RESTIC_VERSION/restic_$RESTIC_VERSION_linux_amd64.bz2 \
	&& bzip2 -dc ./restic.bz2 >> /usr/local/bin/restic \
       && rm -rf ./restic.bz2

# Download kubectl
RUN curl -L -o /usr/local/bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v$KUBECTL_VERSION/bin/linux/amd64/kubectl

COPY kubedrutil.sh /usr/local/bin

# ENTRYPOINT ["/usr/local/bin/restic"]
