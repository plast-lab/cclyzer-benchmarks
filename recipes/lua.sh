# Lua interpreter and bytecode compiler (plain Makefile)
VERSION=5.4.7
URL=https://www.lua.org/ftp/lua-$VERSION.tar.gz
SHA256=9fbf5e28ef86c69858f6d3d34eccc32e911c1a28b4120ff3e84aaa70cfbf1e30
KEEP='^src/(lua|luac)$'
build() {
    make -j"$JOBS" linux CC="$CC" AR="$AR rcu" RANLIB="$RANLIB" MYCFLAGS= MYLDFLAGS=
}
