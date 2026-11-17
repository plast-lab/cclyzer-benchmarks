# GNU Bash
VERSION=5.2.37
URL=https://ftp.gnu.org/gnu/bash/bash-$VERSION.tar.gz
SHA256=9599b22ecd1d5787ad7d3b7bf0c59f312b3396d1e281175dd1f8a4014da621ff
KEEP='^bash$'
build() {
    ./configure --without-bash-malloc --disable-nls
    make -j"$JOBS"
}
