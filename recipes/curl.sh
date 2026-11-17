# curl command-line tool, statically linked with libcurl (no TLS)
VERSION=8.10.1
URL=https://curl.se/download/curl-$VERSION.tar.xz
SHA256=73a4b0e99596a09fa5924a4fb7e4b995a85fda0d18a2c02ab9cf134bebce04ee
KEEP='^src/curl$'
build() {
    ./configure --disable-shared --without-ssl --without-libpsl --without-zlib \
        --without-brotli --without-zstd --without-nghttp2 --without-libidn2 --disable-ldap
    make -j"$JOBS"
}
