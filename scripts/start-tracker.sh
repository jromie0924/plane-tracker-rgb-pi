#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.." || exit 1

AWS_SECRET="$HOME/.aws_secret"

python src/app.py "$AWS_SECRET"
