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

   Note that the `env-shared` component must be created and applied before the API. The portal has no direct dependencies.

1. The command above creates a new directory: `infra/<component>/environments/<new-env>`
1. From the new directory, run:

   ```
   terraform init
   ```

1. Depending on the component you're setting up, you may need to do a few more things outside of Terraform:

   **env-shared / api:**

   - Confirm or configure the variables in `environments/<new-env>/main.tf`.

1. Create the environment:

   **Portal:**

   - Note: When creating a new environment for the Portal, you'll need to set `cloudfront_origin_path` since nothing will be deployed yet:

     ```sh
     terraform plan -var='cloudfront_origin_path='
     ```

     ```sh
     terraform apply -var='cloudfront_origin_path='
     ```

   **Api:**

   - When applying changes, provide an initial application version to deploy. Since this requires a version that is built and pushed to ECR, it's easiest to use the latest version on master.

     ```sh
     $ git rev-parse master
     82043ae1e04621251fb9e7896176b38c884f027e

     $ terraform apply -var='service_docker_tag=82043ae1e04621251fb9e7896176b38c884f027e'
     ```

   **Other components:**

   ```
   terraform plan
   ```

   If everything from the plan looks right, then:

   ```
   terraform apply
   ```

1. Follow additional steps specific to each component:

   - [Additional steps for new Portal environments](portal/creating-environments.md)

1. Add the new environment to the [CI build matrix](/.github/workflows/infra-validate.yml) so it can be validated when it's changed.
