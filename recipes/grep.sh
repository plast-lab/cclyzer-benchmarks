# GNU grep
VERSION=3.11
URL=https://ftp.gnu.org/gnu/grep/grep-$VERSION.tar.xz
SHA256=1db2aedde89d0dea42b16d9528f894c8d15dae4e190b59aecc78f5a951276eab
KEEP='^src/grep$'
build() {
    ./configure --disable-nls --disable-perl-regexp
    make -j"$JOBS"
}
