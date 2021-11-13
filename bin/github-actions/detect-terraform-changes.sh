#!/usr/bin/env bash
set -euo pipefail

USAGE="
Detects whether the given terraform module or any of its local dependencies have changed since the given ref.

args:
FOLDER: path to the root folder.
BASEREF: ref to compare against.

example:
./bin/github-actions/detect-terraform-changes.sh infra/monitoring origin/main
"

if [[ $# != 2 ]]; then
    echo "$USAGE"
    exit 1
fi

echo "::set-output name=has-changes::false"

folder=$1
baseref=$2

find_submodules() (
    folder=$1
    submodules=$(git grep -h 'source\s*=\s*"\.' -- ${folder} | sed 's/.*\"\(.*\)\".*/\1/' | sed s:^:${folder}/:g | xargs realpath)
    echo $(uniqify_list "$submodules")
)

uniqify_list() (
    echo "$1" | xargs -n1 | sort | uniq
)

get_all_dependency_folders() (
    folders="$1"
    folders_to_search="$folders"

    while [[ ! -z "$folders_to_search" ]]; do
        new_folders=""

        for folder in $folders_to_search; do
            echo "Searching for submodules in: $folder" >&2
            submodules=$(find_submodules $folder)
            
            echo "Found submodules: $submodules" >&2
            new_folders="$new_folders $submodules"
        done

        new_folders=$(uniqify_list "$new_folders")
        folders_to_search="$new_folders"

        folders="$folders $new_folders"
        folders=$(uniqify_list "$folders")
        echo "$folders"
    done
)

get_git_diff() (
    folder=$1
    echo "$(git --no-pager diff --name-only $2 ${GITHUB_SHA} -- ${folder})"
)

folders=$(get_all_dependency_folders "$folder")
echo "All dependencies for $folder: $folders"

for folder in $folders; do
    if [ -n "$(get_git_diff $folder $baseref)" ]; then
        echo "::set-output name=has-changes::true"
        break
    fi
done
