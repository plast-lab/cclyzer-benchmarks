# Zstandard compressor CLI
VERSION=1.5.6
URL=https://github.com/facebook/zstd/releases/download/v$VERSION/zstd-$VERSION.tar.gz
SHA256=8c29e06cf42aacc1eafc4077ae2ec6c6fcb96a626157e0593d5e82a34fd403c1
KEEP='^programs/obj/conf_[0-9a-f]+/zstd$'   # linked here, then copied to programs/zstd
build() {
    make -j"$JOBS" -C programs zstd CC="$CC" AR="$AR" HAVE_ZLIB=0 HAVE_LZMA=0 HAVE_LZ4=0
}
