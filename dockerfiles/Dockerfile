FROM quay.io/pypa/manylinux2010_x86_64 as base

RUN set -xe;\
    curl https://sh.rustup.rs -sSf | bash -s -- -y; \
    echo 'source $HOME/.cargo/env' >> $HOME/.bashrc

RUN set -xe; \
    mkdir -p /php/7.4; \
    curl -L https://github.com/php/php-src/archive/php-7.4.1.tar.gz | tar zx -C /php/7.4 --strip-components=1

RUN set -xe; \
    mkdir -p /tmp/src/bison; \
    curl -L https://ftpmirror.gnu.org/gnu/bison/bison-3.0.4.tar.gz | tar zx -C /tmp/src/bison --strip-components=1; \
    cd /tmp/src/bison; \
    ./configure; \
    make install -j $(nproc)


WORKDIR /php/7.4

RUN set -xe; \
    yum install -y re2c libxml2-devel; \
    yum clean all && \
    rm -rf /var/cache/yum


RUN set -xe; \
    ./buildconf --force; \
    ./configure --prefix=/opt/php7.4;

RUN set -xe; \
    make -j 2


# RUN yum -y update; yum -y install curl
# RUN set -xe; 
    # yum -y update; \
    # yum -y install curl

# FROM centos:6 as test