# PostgreSQL: the server and the client tools, each linked with libpgport/libpgcommon
VERSION=16.4
URL=https://ftp.postgresql.org/pub/source/v$VERSION/postgresql-$VERSION.tar.bz2
SHA256=971766d645aa73e93b9ef4e3be44201b4f45b5477095b049125403f9f3386d6f
KEEP='^src/backend/postgres$|^src/bin/[^/]+/[^/.]+$|^src/interfaces/ecpg/preproc/ecpg$'
EXCLUDE='/(tmp_check|t)/'
build() {
    ./configure --without-icu --without-readline --without-zlib --without-openssl
    make -j"$JOBS"
}
