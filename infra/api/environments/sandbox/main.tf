provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-sandbox"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf_lock"
  }
}

data "aws_ecs_cluster" "sandbox" {
  cluster_name = "sandbox"
}

module "api" {
  source = "../../template"

  environment_name        = "sandbox"
  service_app_count       = 2
  service_docker_tag      = local.service_docker_tag
  service_ecs_cluster_arn = data.aws_ecs_cluster.sandbox.arn
  vpc_id                  = data.aws_vpc.nava_internal.id
  vpc_app_subnet_ids      = data.aws_subnet_ids.nava_internal_app.ids
  postgres_version        = "11.6"
  nlb_name                = "sandbox-nlb"
  nlb_port                = "80"
  cors_origins            = ["https://pfml.navateam.com", "https://pfml-sandbox-v2.navateam.com"]
}
