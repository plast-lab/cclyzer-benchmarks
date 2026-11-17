# GNU gzip
VERSION=1.13
URL=https://ftp.gnu.org/gnu/gzip/gzip-$VERSION.tar.xz
SHA256=7454eb6935db17c6655576c2e1b0fabefd38b4d0936e0f87f48cd062ce91a057
KEEP='^gzip$'
build() {
    ./configure
    make -j"$JOBS"
}
