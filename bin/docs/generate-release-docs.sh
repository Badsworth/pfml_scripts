#!/usr/bin/env bash
#
# Generates release pages. These document the current release on each environment, and what changes are next up from the main branch.
#

regex_escape_all () {
    while read data; do
        echo $data | sed -E 's/([/. ?()])/\\\1/g'
    done
}

regex_escape_pipes () {
    while read data; do
        echo $data | sed -E 's/([| ])/\\\1/g'
    done
}


mkdir -p docs/releases

declare -A components
# A key/value pair of the component name and directory.
components[api]=api
components[portal]=portal
components[admin-portal]=admin

for component in "${!components[@]}"; do
    directory="${components[$component]}"
    # Grab the version tag, if it exists, and create a link to the Github release page around it.
    #
    # e.g.
    # old: api/v1.1.0
    # new: <a href="...">api/v1.1.0</a>
    #
    VERSION_CAPTURE="([^/])($component\/v[^ |)]*)"
    GITHUB_RELEASE_LINK_FORMAT=$(echo '\\\1<a href="https://github.com/EOLWD/pfml/releases/tag/\\\2">\\\2</a>' | regex_escape_all)

    # Grab "dirty" version tags and parse them, linking to the latest commit and the diff from the latest tag.
    #
    # e.g.
    # old: api/v1.1.0-2-gabcd
    # new: api/v1.1.0 (2 commits ahead on abcd)
    #
    DIRTY_CAPTURE="($component\/v.*)-([0-9]+)-g(.*)"
    DIRTY_FORMAT=$(echo '<a href="https://github.com/EOLWD/pfml/commits/\\\3">\\\3</a> \(<a href="https://github.com/EOLWD/pfml/compare/\\\1...\\\3">\\\2 commits ahead</a> of \\\1)' | regex_escape_all)

    # Grab the first two columns, i.e. the environment name and release version.
    # Insert them back in as-is, then add a link to the GH Deployments page for the environment.
    #
    # e.g.
    # old: |test|api/v1.1.0
    # new: |test|api/v1.1.0|<a href="...">GitHub</a>
    #
    ENV_CAPTURE=$(echo ' | *(.*)|(.*)$' | regex_escape_pipes)
    ENV_REPLACE=$(echo ' |\\\1|\\\2|' | regex_escape_pipes)
    GITHUB_DEPLOYMENTS_FORMAT=$(echo '<a href="https://github.com/EOLWD/pfml/deployments/activity_log?environment='$component'+(\\\1)">GitHub</a>' | regex_escape_all)

    released=$(make -s -C $directory whats-released-short |
                   sed -E "s/origin\/(deploy\/$component\/)?//g" |
                   sed -E 's/main/test/g' |
                   sed -E 's/(\*|:)/\|/g' |
                   sed -E "s/$DIRTY_CAPTURE/$DIRTY_FORMAT/g" |
                   sed -E "s/$VERSION_CAPTURE/$GITHUB_RELEASE_LINK_FORMAT/g" |
                   sed -E "s/$ENV_CAPTURE/$ENV_REPLACE$GITHUB_DEPLOYMENTS_FORMAT/g")

    tickets=$(make -s -C $directory release-list)

    if [[ $component == 'api' ]]; then
        CONFLUENCE_NOTES='https://lwd.atlassian.net/wiki/spaces/DD/pages/1086226543/2021+Releases'
    elif [[ $component == 'portal' ]]; then
        CONFLUENCE_NOTES='https://lwd.atlassian.net/wiki/spaces/DD/pages/819036412/Portal+Release+Notes'
    else
        CONFLUENCE_NOTES='https://lwd.atlassian.net/wiki/spaces/DD/pages/2189755940/Admin+Portal+Release+Notes'
    fi

    cat > docs/releases/$component.md <<EOF
|environment|release|deployments|
|----|----|----|
$released

Full release notes are available in [Confluence]($CONFLUENCE_NOTES).

Next Release ([Jira List](https://lwd.atlassian.net/issues/?jql=id in ($tickets))):

$(make -s -C $directory release-notes | sort -r)

<details>
<summary>Raw</summary>
$(make -s -C $directory release-notes | sort -r | sed -E 's/\*/<br\>\*/g')
</details>
EOF
done
