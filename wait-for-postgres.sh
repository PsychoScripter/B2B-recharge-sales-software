#!/bin/sh
set -e

host="$1"
shift
cmd="$@"

echo "منتظر PostgreSQL..."
until pg_isready -h "$host" -U "$POSTGRES_USER"; do
  echo "Postgres در دسترس نیست، ۲ ثانیه صبر می‌کنم"
  sleep 2
done

echo "Postgres آماده است، دستور اجرا می‌شود"
exec $cmd
