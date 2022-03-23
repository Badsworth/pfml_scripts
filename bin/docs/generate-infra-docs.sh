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

for COMPONENT in infra; do
    tickets=$(make -s -C $COMPONENT release-list)
    CONFLUENCE_NOTES='https://lwd.atlassian.net/wiki/spaces/DD/pages/2160197653/BI+2022+Releases'

    cat > docs/releases/$COMPONENT.md <<EOF

This page reflects Infrastructure changes that have been released. Changes to  Business Intelligence can be found here as well. Expect this page to be quieter compared to the API, Portal and Admin Portal pages.

Full release notes are available in [Confluence]($CONFLUENCE_NOTES).

Next Release ([Jira List](https://lwd.atlassian.net/issues/?jql=id in ($tickets))):

$(make -s -C $COMPONENT release-notes | sort -r)

<details>
<summary>Raw</summary>
$(make -s -C $COMPONENT release-notes | sort -r | sed -E 's/\*/<br\>\*/g')
</details>
EOF
done
