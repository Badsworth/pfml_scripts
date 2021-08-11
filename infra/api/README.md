# API Infrastructure

Infrastructure for the Paid Leave API is defined in this directory.

## Pre-requisites

This infra is designed to be deployed within an EOTSS-managed VPC, with private application and database subnets. The VPC must have a pre-existing ECS cluster and network load balancer (NLB) which can be connected to with the provided `nlb_port` variable; this is usually set up in the [infra/pfml-aws](../pfml-aws) module. 

see [Creating Environments](../../docs/creating-environments.md). 

Note that the infrastructure deployed by this module does not provide public access to the Paid Leave API. Instead, this module sets up listeners on the network load balancer on `nlb_port`, and forwards those requests to the private API servers.

The API Gateway, which receives public requests and securely routes it to the private NLB, is set up in [infra/env-shared](../env-shared/).

## Key Components

### RDS Database

An RDS database is created in the provided database subnets in [rds.tf](./template/rds.tf). Note that once created, future configuration and administrative actions are managed by the Smartronix Managed Services DB administrators.

### Paid Leave API

The Paid Leave API is deployed on containers using ECS Fargate. This is defined in [service.tf](./template/service.tf) and the accompanying [container_definitions.json](./template/container_definitions.json) template.

The API is configured with auto-scaling based on the average CPU utilization across all of the containers. New containers are automatically added at high CPU percentages, and removed during periods of low CPU usage.

This is defined in [autoscaling-ecs.tf](./template/autoscaling-ecs.tf).

## Log Destinations

Logs for the RDS database and Paid Leave API are sent to cloudwatch and forwarded to New Relic using the global New Relic lambda forwarder, as specified in [cloudwatch.tf](./template/cloudwatch.tf).

## Deployment

This module is deployed through the API CI Deploy workflow in Github Actions. See: [docs/deployment.md](../../docs/deployment.md).
