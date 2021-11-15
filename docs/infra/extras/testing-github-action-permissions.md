# Testing Github Actions permissions

Since Github Actions has different permissions than developers and admins, it's useful to test terraform configs using our CI/CD role so we know
that they can be run on Github Actions with the right read/write permissions. This is recommended if you're adding a new service into our ecosystem.

1. Ensure you have the AWS CLI:

   ```
   pip install awscli
   ```

2. Generate a session:

   ```
   aws sts assume-role --role-arn arn:aws:iam::498823821309:role/ci-run-deploys --role-session-name <any-session-name>
   ```

3. Copy the access key, secret, and session token into your ~/.aws/credentials under a new profile so it looks like this:

   ```
   [ci-run-deploys]
   aws_access_key_id = 123
   aws_secret_access_key = 456
   aws_session_token = 789
   ```

4. Use the profile:

   ```
   export AWS_PROFILE=ci-run-deploys
   ```

5. Run terraform as usual.

Alternatives to steps 3-4 are using [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) or using the AWS CLI ([aws configure](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)).
