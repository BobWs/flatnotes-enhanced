#!/bin/sh

[ "$EXEC_TOOL" ] || EXEC_TOOL=gosu
[ "$FLATNOTES_HOST" ] || FLATNOTES_HOST=0.0.0.0
[ "$FLATNOTES_PORT" ] || FLATNOTES_PORT=8080

set -e

# Extract version from package.json
VERSION=$(grep -m1 '"version"' /app/package.json | cut -d'"' -f4)

echo "\
===============================================
======== Welcome to Flatnotes-Enhanced ========
===============================================

Version: v${VERSION}

Thank you for using Flatnotes-Enhanced!

If you enjoy using flatnotes-enhanced, please
consider sponsoring this forked project.

It would really make my day 🙏.

──────────────────────────────────────
"

flatnotes_command="python -m \
                  uvicorn \
                  main:app \
                  --app-dir server \
                  --host ${FLATNOTES_HOST} \
                  --port ${FLATNOTES_PORT} \
                  --proxy-headers \
                  --forwarded-allow-ips '*'"

if [ `id -u` -eq 0 ] && [ `id -g` -eq 0 ]; then
    echo Setting file permissions on data folder...
    chown -R ${PUID}:${PGID} ${FLATNOTES_PATH}

    echo Setting permissions on web files...
    chown -R ${PUID}:${PGID} ${APP_PATH}/client/dist

    echo Starting flatnotes as user ${PUID}...
    exec ${EXEC_TOOL} ${PUID}:${PGID} ${flatnotes_command}

else
    echo "A user was set by docker, skipping file permission changes."
    echo Starting flatnotes as user $(id -u)...
    exec ${flatnotes_command}
fi