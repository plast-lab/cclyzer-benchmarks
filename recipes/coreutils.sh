# GNU coreutils: every program in src/, each linked with libcoreutils and gnulib
VERSION=9.5
URL=https://ftp.gnu.org/gnu/coreutils/coreutils-$VERSION.tar.xz
SHA256=cd328edeac92f6a665de9f323c93b712af1858bc2e0d88f3f7100469470a1b8a
KEEP='^src/[^/]+$'
EXCLUDE='\.so$|^src/make-prime-list$'
build() {
    ./configure --disable-nls --without-selinux --without-openssl --disable-libcap
    make -j"$JOBS"
}
