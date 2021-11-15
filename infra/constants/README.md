# constants

A small module that outputs shared values for other modules to use.

## Usage

Example usage:

```tf
# 1. Import the constants module
module "constants" {
  source = "../constants"
}

resource "aws_cloudwatch_log_group" "my_log_group" {
  name = "my-log-group"

  # 2.  Use the constants module output values
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
```
