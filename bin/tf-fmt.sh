#!/usr/bin/env bash
#
# Format terraform files.
#
USAGE="Usage: tf-fmt.sh [FILE ...]
If no files are given, defaults to formatting all terraform files."

if [[ "$1" == *"help"* ]]; then
    echo "$USAGE"
    exit 0
fi

if ! [ -x "$(command -v terraform)" ]; then
    echo "⚠️  terraform is not installed; please see infra/README.md for installation."
    echo "exiting safely."
    exit 0
fi

if [ $# -eq 0 ]; then
    # Default to recursively formatting infra/
    # if files were not provided as arguments.
    terraform fmt -recursive infra/
else
    FILES=$*
    for a in $FILES; do terraform fmt $a; done
fi
