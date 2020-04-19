FROM quay.io/pypa/manylinux2010_x86_64 as base

COPY build_php.sh prepare_build.sh /tmp/
RUN /tmp/prepare_build.sh
RUN /tmp/build_php.sh 7.4 https://github.com/php/php-src/archive/php-7.4.1.tar.gz
RUN /tmp/build_php.sh 7.3 https://github.com/php/php-src/archive/php-7.3.1.tar.gz
RUN /tmp/build_php.sh 7.2 https://github.com/php/php-src/archive/php-7.2.1.tar.gz
RUN /tmp/build_php.sh 7.1 https://github.com/php/php-src/archive/php-7.1.1.tar.gz
RUN /tmp/build_php.sh 7.0 https://github.com/php/php-src/archive/php-7.0.1.tar.gz
RUN /tmp/build_php.sh 5.6 https://github.com/php/php-src/archive/php-5.6.30.tar.gz

FROM scratch as tmp
COPY --from=tmp /opt/php7.4 /opt/php7.3 /opt/php7.2 /opt/php7.1 /opt/php7.0 /opt/php5.6 /opt/

FROM quay.io/pypa/manylinux2010_x86_64 as target
COPY --from=tmp /opt/ /opt/

RUN set -xe;\
    curl https://sh.rustup.rs -sSf | bash -s -- -y; \
    echo 'source $HOME/.cargo/env' >> $HOME/.bashrc

RUN set -xe; \
    mkdir -p /work; \
    cd /work; \
    git clone https://github.com/DataDog/dd-trace-php; 
