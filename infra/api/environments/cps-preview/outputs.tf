output "ecs_cluster_arn" {
  value = data.aws_ecs_cluster.cps-preview.arn
}

output "ecs_service_id" {
  value = module.api.ecs_service_id
}
