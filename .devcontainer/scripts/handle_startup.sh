#!/bin/bash

if ["$DEV_CONTAINER" = "true"]; then
    echo "Connecting to dev container"
    tail -f /dev/null
else
    cp devcontainer/example.env .env
    echo "Reproducing results"
    conda run -n netlogo python simulation/main.py
fi