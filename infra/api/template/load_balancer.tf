data "aws_lb" "network_load_balancer" {
  name = var.nlb_name
}

# Forward HTTP traffic to the application.
# Since we're directing traffic from a private API gateway, we don't need to use HTTPS.
resource "aws_lb_listener" "listener" {
  load_balancer_arn = data.aws_lb.network_load_balancer.id
  port              = var.nlb_port
  protocol          = "TCP"

  default_action {
    target_group_arn = aws_lb_target_group.app.id
    type             = "forward"
  }
}

# Define the application target to route HTTP traffic from API Gateway to the API.
resource "aws_lb_target_group" "app" {
  name                 = "${local.app_name}-${var.environment_name}"
  port                 = var.nlb_port
  protocol             = "TCP"
  vpc_id               = var.vpc_id
  target_type          = "ip"
  deregistration_delay = 20

  health_check {
    protocol            = "HTTP"
    path                = "/v1/status"
    healthy_threshold   = 8
    unhealthy_threshold = 8
  }
}
