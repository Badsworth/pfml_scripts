# Setting up a new environment

The easiest way to set up resources in a new environment is using the templates in [/bin/bootstrap-env/](../bin/bootstrap-env).

1. The S3 bucket for holding tfstate files must be created first in [infra/pfml-aws/s3.tf](../infra/pfml-aws/s3.tf)
1. Then, individual terraform components (`env-shared`, `api`, or `portal`) may be set up.

    ```
    pfml$ bin/bootstrap-env/bootstrap-env.sh <new-env> <component>
    ```

    For example:

    ```
    pfml$ bin/bootstrap-env/bootstrap-env.sh test portal
    ```

1. The command above creates a new directory: `infra/<component>/environments/<new-env>`
1. From the new directory, run:
    ```
    terraform init
    ```
1. Depending on the component you're setting up, you may need to do a few more things outside of Terraform:

    **Portal:**
    - Confirm or configure the variables in `environments/<new-env>/main.tf`

      By default, new environments are configured to NOT send emails through SES. This is fine for development, but for production-like environments, this should be changed. An email must be verified before it can be used by SES. If you configure an environment to use SES with an unverified email, when you first run `terraform apply` it will fail, and report that you need to verify the email address.
1. Create the environment:

    **Portal:**
    - Note: When creating a new environment for the Portal, you'll need to set `cloudfront_origin_path` since nothing will be deployed yet:

        ```sh
        terraform plan -var='cloudfront_origin_path='
        ```

        ```sh
        terraform apply -var='cloudfront_origin_path='
        ```

    **Other components:**
    ```
    terraform plan
    ```

    If everything from the plan looks right, then:

    ```
    terraform apply
    ```