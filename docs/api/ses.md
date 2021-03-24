## Configuring ECS Tasks to send emails

In certain cases, it may make sense to send emails from a running application. The instructions below list out the required steps for getting your ECS task configured with the appropriate permissions.

### Allow your task IAM Role to send emails

By default, your ECS task does not have any AWS permissions. IAM roles define what they are allowed to do, with which resources (like an SES email!) There are two IAM roles for a task: the task IAM role and the execution IAM role.

- The task IAM role defines the permissions used during application runtime.

- The execution IAM role defines the permissions needed before the task starts.

Since you'll be sending emails during an application's runtime, the task IAM role policy will need to be configured with permissions to send emails. This might look like this:

```tf
  statement {
    sid    = "AllowSESSendEmail"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    condition {
      test     = "ForAllValues:StringLike"
      variable = "ses:Recipients"
      values = [
        # Any email addresses you expect to communicate with.
      ]
    }

    resources = [
      "*"
    ]
  }
```

### Add your IAM role name to the SES allowlist

Additionally, we maintain a strict list of resources that are allowed to send emails with each of our email addresses in [ses.tf](/infra/pfml-aws/ses.tf). You'll want to update the condition in `data.aws_iam_policy_document.restrict_ses_senders` to include your IAM roles in this pattern:

```tf
arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/MY_IAM_ROLE_PATTERN/*"
```

Note that this is the name of the IAM role itself, not the policy. e.g. use the name in this block:

```tf
resource "aws_iam_role" "payments_fineos_process_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-payments-fineos-process"
  ...
}
```
