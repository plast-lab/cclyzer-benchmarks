# GNU tar
VERSION=1.35
URL=https://ftp.gnu.org/gnu/tar/tar-$VERSION.tar.xz
SHA256=4d62ff37342ec7aed748535323930c7cf94acf71c3591882b26a7ea50f3edc16
KEEP='^src/tar$'
build() {
    ./configure --disable-nls
    make -j"$JOBS"
}
