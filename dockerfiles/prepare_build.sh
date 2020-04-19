#!/bin/bash -xe

mkdir -p /tmp/src/bison
curl -L https://ftpmirror.gnu.org/gnu/bison/bison-3.0.4.tar.gz | tar zx -C /tmp/src/bison --strip-components=1
cd /tmp/src/bison
./configure
make install -j $(nproc)

yum install -y re2c libxml2-devel
yum clean all
rm -rf /var/cache/yum
