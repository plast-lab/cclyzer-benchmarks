# git and its standalone helper programs
VERSION=2.47.0
URL=https://mirrors.edge.kernel.org/pub/software/scm/git/git-$VERSION.tar.xz
SHA256=1ce114da88704271b43e027c51e04d9399f8c88e9ef7542dae7aebae7d87bc4e
KEEP='^(git|git-daemon|git-shell|git-http-backend|git-imap-send)$'
build() {
    make -j"$JOBS" CC="$CC" AR="$AR" NO_OPENSSL=1 NO_CURL=1 NO_EXPAT=1 NO_GETTEXT=1 \
        NO_TCLTK=1 NO_PERL=1 NO_PYTHON=1 CFLAGS= LDFLAGS= all
}
