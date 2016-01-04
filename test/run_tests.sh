#!/usr/bin/env bash

SCRIPT_DIR=$(dirname `realpath $0`)

PYTHONPATH=$SCRIPT_DIR/../bin python3 $SCRIPT_DIR/input_output_tests.py
