#!/bin/bash
# Compatibility entry. The complete package uses START_HERE_MAC.command.
exec /bin/bash "$(dirname "$0")/START_HERE_MAC.command" --cost-check
