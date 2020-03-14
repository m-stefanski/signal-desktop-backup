# signal-desktop-export

This script is a result of the frustration I felt when I realized there is no way to create export for Signal for Desktop conversations.

Then, few additional hours of frustration spent to find out how to get python to read SQLite databases that have been encrypted with sqlcipher.

This is not a user-friendly tool, rather a starting point for further development.

As of now, only MacOS version is available. Should be compatible with Cathalina (removed 32-bit support).

## Dependencies

* Python 3
* XCode command line tools

## Usage

**After** properly installed, run ```python signal_desktop_export.py```. 

```signal_export_YYYYMMDD_HHMMSS``` folder should appear, together with conversations exported as html.

If you get an error alike ```ModuleNotFoundError: No module named 'pysqlcipher3'```, please make sure you followed the steps below.

## Installation

### Automatic

To install dependencies, run ```install_dependencies_macos.sh```, you will be asked for sudo password during dependencies installation steps - they are required to make install openssl and sqlcipher libraries. 

Alternatively, you can use the manual instruction below.

### Manual (if you don't trust me, and you shouldn't)

First, create and populate virtual environment for the tool:

```
python3 -m venv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

You need sqlcipher static files which are required for the pip to install pysqlcipher successfully. 

For some reason it will not tell you that, but simply fail. To fix this, we will have to go through some compiling.

First, download and compile OpenSSL which is a depencency for sqlcipher:

```
git clone git://git.openssl.org/openssl.git
cd openssl
./Configure darwin64-x86_64-cc shared enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-comp --openssldir=/usr/local/ssl/macos-x86_64
make depend
sudo make install
```

Then go back to the project root directory and clone and compile sqlcipher library:

```
cd ..
git clone https://github.com/sqlcipher/sqlcipher.git
cd sqlcipher
./configure --enable-tempstore=yes CFLAGS="-DSQLITE_HAS_CODEC -I/usr/local/include/openssl/" LDFLAGS="/usr/local/lib/libcrypto.a"
sudo make install 
```

After that you should be able to build and install pysqlcipher3 (starting again from project root directory):

```
cd ..
git clone https://github.com/rigglemania/pysqlcipher3.git
cd pysqlcipher3
python setup.py build
python setup.py install
```
