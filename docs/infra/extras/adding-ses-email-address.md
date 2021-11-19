# Adding a new SES email address

In order to send emails from an SES email address, the email must first be verified.
Ensure you have someone who can access the inbox of the email you'll be setting, so they can verify it.

## Creating the email in Terraform

1. Create an ses_email_address resource.
1. Run `terraform apply`, which will likely return an error indicating you need to verify the email address.
1. Verify the email address by clicking the link in the verification email that should have been sent after the previous step.
1. Run `terraform apply` again, which should be successful this time.

## Creating the email in AWS Console

Alternatively, you can create the email in the AWS Console and verify it:

1. Add the email to SES through the AWS Console
1. Verify the email address by clicking the link in the verification email that should have been sent after the previous step.
1. Import the SES email resource:
    ```
    terraform import aws_ses_email_identity.example email@example.com
    ```
