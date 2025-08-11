#!/bin/bash

set -euo pipefail

nginx &
python3 ./main.py &

wait -n
exit $?
