# GNU sed
VERSION=4.9
URL=https://ftp.gnu.org/gnu/sed/sed-$VERSION.tar.xz
SHA256=6e226b732e1cd739464ad6862bd1a1aba42d7982922da7a53519631d24975181
KEEP='^sed/sed$'
build() {
    ./configure --disable-nls
    make -j"$JOBS"
}
