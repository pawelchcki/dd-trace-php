#/bin/bash -xe

DIR=/tmp/php/$1
OUTPUT=/opt/php$1
URL=$2
mkdir -p $DIR
curl -L $URL | tar zx -C $DIR --strip-components=1
cd $DIR

./buildconf --force
./configure --prefix=$OUTPUT

make -j 2

make -j 2 install