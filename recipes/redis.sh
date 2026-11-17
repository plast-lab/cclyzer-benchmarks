# Redis server, CLI and benchmark, with bundled hiredis, lua and friends
VERSION=7.2.6
URL=https://download.redis.io/releases/redis-$VERSION.tar.gz
SHA256=fb10d67a2fe2b4556f6cb840064dd6e6e3175ce8ca035f0726990ec2da9f3d0e
KEEP='^src/redis-(server|cli|benchmark)$'
build() {
    make -j"$JOBS" MALLOC=libc BUILD_TLS=no USE_SYSTEMD=no CC="$CC" AR="$AR"
}
