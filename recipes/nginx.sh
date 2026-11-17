# nginx web server (modules reached through function-pointer tables)
VERSION=1.26.2
URL=https://nginx.org/download/nginx-$VERSION.tar.gz
SHA256=627fe086209bba80a2853a0add9d958d7ebbdffa1a8467a5784c9a6b4f03d738
KEEP='^objs/nginx$'
build() {
    ./configure --with-cc="$CC" --without-http_rewrite_module --without-http_gzip_module
    make -j"$JOBS"
}
