provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "stage"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id

  fineos_client_customer_api_url     = "https://idt-api.masspfml.fineos.com/customerapi/"
  fineos_client_group_client_api_url = "https://idt-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url   = "https://idt-claims-webapp.masspfml.fineos.com/wscomposer/"
  fineos_client_oauth2_url           = "https://idt-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id     = "1fa281uto9tjuqtm21jle7loam"

  fineos_aws_iam_role_arn         = "arn:aws:iam::016390658835:role/sompre-IAMRoles-CustomerAccountAccessRole-S0EP9ABIA02Z"
  fineos_aws_iam_role_external_id = "8jFBtjr4UA@"

  fineos_eligibility_feed_output_directory_path = "s3://fin-somdev-data-import/IDT/absence-eligibility/upload"
}
