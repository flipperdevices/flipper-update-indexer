#!/bin/bash

nginx &
python3 ./main.py &

wait -n
exit $?
