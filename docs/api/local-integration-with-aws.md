# Local Integration with AWS

In some cases, we need to make requests to AWS services directly. If running locally, you will need to ensure that your environment has appropriate credentials.

- See [Configure AWS](./infra/1-first-time-setup.md#1-configure-aws) for details on setting up the AWS command line locally.
- Once set up, the credentials need to be placed into the Docker container. Follow the instructions in [docker-compose.override.yml](/api/docker-compose.override.yml).

(For more information on how setting environment variables work, see: [Environment Variables](/docs/api/environment-variables.md))
