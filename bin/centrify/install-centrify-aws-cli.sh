#!/usr/bin/env bash
#
# Script for installing and wrapping the Centrify AWS login script on developer machines.
#
# You need to run this if you:
#   - work with the AWS CLI directly, or
#   - run terraform from your machine to view and manage AWS resources.
#
# After running this script, you'll have a new runnable command. This command
# prompts you to login to EOTSS Centrify, after which it configures your AWS
# credentials with a 1-hour AWS access key.
#
set -euo pipefail

USAGE="
Usage: Sets up the Centrify AWS CLI script environment and creates a global login command.

./install-centrify-aws-cli.sh INSTALL_LOCATION

args:
  INSTALL_LOCATION - The location to pull down the Centrify AWS CLI git repo and install the wrapper script.

example:
  ./install-centrify-aws-cli.sh ~/code/git/
"

if [[ $# != 1 ]]; then
    echo "$USAGE"
    exit 1
fi

echo
read -p "Enter the command name you want to use to log into AWS.
(default: login-aws): " CMD_NAME

read -p "
Enter a location to install the command.
- Should be in your PATH (recommended)
- If installing on *nix to a system location, rerun this script as root.
- Absolute or expandable (~/) paths please :)

(default: /usr/local/bin): " CMD_LOCATION

INSTALL_LOCATION=$1
CMD_LOCATION=${CMD_LOCATION:-/usr/local/bin}
CMD_NAME=${CMD_NAME:-login-aws}

# Grab the absolute path of the companion script, login-aws-template.sh.
# We'll need to copy this script later to a different directory.
#
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
LOGIN_AWS_SCRIPT_PATH=$SCRIPT_PATH/login-aws-template.sh
CACERTS_PATH=$SCRIPT_PATH/cacerts_eotss.pem

# 1. Go to the install location.
pushd $INSTALL_LOCATION

# 2. Download centrify-aws-cli-utilities.
if ! [ -d "centrify-aws-cli-utilities" ]; then
    # Try with SSH first, then user/password over HTTPS.
    git clone git@github.com:centrify/centrify-aws-cli-utilities.git || git clone https://github.com/centrify/centrify-aws-cli-utilities.git
fi

pushd centrify-aws-cli-utilities/Python-AWS

# 3. Copy SSL certificates for the Centrify endpoint.
#    The filename is important and should match the centrify URL target
#    (eotss.my.centrify.com). This allows us to securely make requests to Centrify.
#
#    Originally generated with the following commands (now broken):
#
#    openssl s_client -showcerts -connect eotss.my.centrify.com:443 | \
#    sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > cacerts_eotss.pem
#
#    DIGICERT_GLOBAL_ROOT_SRC="https://dl.cacerts.digicert.com/DigiCertGlobalRootCA.crt.pem"
#    curl $DIGICERT_GLOBAL_ROOT_SRC >> cacerts_eotss.pem
#
cp $CACERTS_PATH cacerts_eotss.pem

# 4. Generate the login-aws script
cp $LOGIN_AWS_SCRIPT_PATH $CMD_NAME.sh
chmod +x $CMD_NAME.sh

# 5. Sym-link the script to a command that is runnable in any directory.
ln -s $(pwd)/$CMD_NAME.sh $CMD_LOCATION/$CMD_NAME

echo
echo "Installation complete! Run $CMD_NAME anytime you need to login to AWS."
