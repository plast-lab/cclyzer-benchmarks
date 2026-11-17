# GNU make
VERSION=4.4.1
URL=https://ftp.gnu.org/gnu/make/make-$VERSION.tar.gz
SHA256=dd16fb1d67bfab79a72f5e8390735c49e3e8e70b4945a15ab1f81ddb78658fb3
KEEP='^make$'
build() {
    ./configure --disable-nls --without-guile
    make -j"$JOBS"
}
