# SQLite command-line shell (amalgamation: one large translation unit plus shell.c)
VERSION=3.46.1
URL=https://www.sqlite.org/2024/sqlite-autoconf-3460100.tar.gz
SHA256=67d3fe6d268e6eaddcae3727fce58fcc8e9c53869bdd07a0c61e38ddf2965071
KEEP='^sqlite3$'
build() {
    ./configure --disable-shared --disable-readline --disable-editline
    make -j"$JOBS"
}
