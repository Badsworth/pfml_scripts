# Local Integration with AWS

In some cases, we need to make requests to AWS services directly. If running locally, you will need to ensure that your environment has appropriate credentials.

Credentials can be obtained by signing in to AWS, and selecting "Command line or programmatic access"

These credentials need to be placed in an AWS creds file (`~/.aws/credentials` or `~/.aws/config`)

Then docker needs to know where to look for these credentials. Follow instructions in `docker-compose.override.yml`

(See also: [the Environment Variables doc](/docs/api/environment-variables.md))
