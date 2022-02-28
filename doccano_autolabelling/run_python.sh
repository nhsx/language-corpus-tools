#!/bin/sh

cd ../appstack/local-docker; . ./env-local; cd -

exec python3 "$@"
