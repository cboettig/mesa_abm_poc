#!/bin/bash

curl -fsSL https://pixi.sh/install.sh | bash
export "eval "$(pixi completion --shell bash)" >> ~/.bashrc