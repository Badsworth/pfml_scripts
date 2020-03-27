#!/usr/bin/env bash -e
#
# In aws-amplify-react (v3.x), it imports a CSS file from its JS file.
# This breaks server-side rendering in Next.js. It can be resolved with
# a Webpack hack, but that introduces its own issues with React hooks.
# https://github.com/aws-amplify/amplify-js/issues/3854
#
# This script is intendend to be ran after `npm install`, and it removes
# the offending lines from aws-amplify-react.
#
# TODO (https://lwd.atlassian.net/browse/CP-231): This script becomes irrelvant
# once the following PR is released, which should happen in v4.x of the library.
# (It shouldn't break anything if it's not removed though).
# https://github.com/aws-amplify/amplify-js/pull/5138

NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[0;33m'

printf "${BLUE}🚮 Removing CSS-in-JS imports from aws-amplify-react (https://lwd.atlassian.net/browse/CP-231)...\n${NC}"

# There are two different versions of the file we need to remove the import from, each
# are used by Next.js in different contexts (server vs client-side)
LIB_DIR="node_modules/aws-amplify-react/lib/"
LIB_ESM_DIR="node_modules/aws-amplify-react/lib-esm/"
FILENAME="Amplify-UI/Amplify-UI-Components-React.js"
COMMONJS_FILE=$LIB_DIR$FILENAME
ESM_FILE=$LIB_ESM_DIR$FILENAME

# The offending lines
COMMONJS_IMPORT='require("@aws-amplify/ui/dist/style.css");'
ESM_IMPORT="import '@aws-amplify/ui/dist/style.css';"

# Replace the offending lines
REPLACEMENT_VALUE="// CSS-in-JS line removed by PFML build system (https://lwd.atlassian.net/browse/CP-231)"

if [ -f "$COMMONJS_FILE" ]; then
    sed -i.bak s+"$COMMONJS_IMPORT"+"$REPLACEMENT_VALUE"+ $COMMONJS_FILE
else
    printf "${YELLOW}${COMMONJS_FILE} doesn't exist.\n${NC}"
fi

if [ -f "$ESM_FILE" ]; then
    sed -i.bak s+"$ESM_IMPORT"+"$REPLACEMENT_VALUE"+ $ESM_FILE
else
    printf "${YELLOW}${ESM_FILE} doesn't exist.\n${NC}"
fi