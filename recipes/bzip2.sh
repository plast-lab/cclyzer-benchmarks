# bzip2 compressor (plain Makefile)
VERSION=1.0.8
URL=https://sourceware.org/pub/bzip2/bzip2-$VERSION.tar.gz
SHA256=ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269
KEEP='^(bzip2|bzip2recover)$'
build() {
    make -j"$JOBS" CC="$CC" AR="$AR" RANLIB="$RANLIB" CFLAGS="-D_FILE_OFFSET_BITS=64" bzip2 bzip2recover
}
