#!/usr/bin/env bash

#
# Script to update sqlite3 to a version which will not segfault
# in out Django unit tests.
#

curl https://codeload.github.com/ghaering/pysqlite/tar.gz/2.8.3 > pysqlite-2.8.3.tar.gz
curl https://www.sqlite.org/2016/sqlite-autoconf-3140100.tar.gz > sqlite-autoconf-3140100.tar.gz
tar -xzvf sqlite-autoconf-3140100.tar.gz
tar -xzvf pysqlite-2.8.3.tar.gz
cp -av sqlite-autoconf-3140100/. pysqlite-2.8.3/
cd ./pysqlite-2.8.3 && python setup.py build_static install

cd ..
rm -rf pysqlite-2.8.3*
rm -rf sqlite-autoconf-3140100*
rm upgrade_sqlite.sh
