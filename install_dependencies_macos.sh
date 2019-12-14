#!/bin/bash

# venv

python3 -m venv venv
source ./venv/bin/activate
pip install -r ./requirements.txt

# openssl 

git clone git://git.openssl.org/openssl.git
cd openssl
./Configure darwin64-x86_64-cc shared enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-comp --openssldir=/usr/local/ssl/macos-x86_64
make depend
sudo make install

cd ..

# sqlcipher

git clone https://github.com/sqlcipher/sqlcipher.git
cd sqlcipher
./configure --enable-tempstore=yes CFLAGS="-DSQLITE_HAS_CODEC -I/usr/local/include/openssl/" LDFLAGS="/usr/local/lib/libcrypto.a"
sudo make install 

cd ..

# pysqlcipher3

git clone https://github.com/rigglemania/pysqlcipher3.git
cd pysqlcipher3
python setup.py build
python setup.py install