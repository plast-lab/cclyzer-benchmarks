# jq JSON processor, with its bundled oniguruma regex library
VERSION=1.7.1
URL=https://github.com/jqlang/jq/releases/download/jq-$VERSION/jq-$VERSION.tar.gz
SHA256=478c9ca129fd2e3443fe27314b455e211e0d8c60bc8ff7df703873deeee580c2
KEEP='^jq$'
build() {
    ./configure --with-oniguruma=builtin --disable-docs --disable-maintainer-mode --disable-shared
    make -j"$JOBS"
}
