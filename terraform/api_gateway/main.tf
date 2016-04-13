provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  region = "${var.aws_region}"
}

resource "aws_api_gateway_rest_api" "ApiGateway" {
  name = "edx.org API Gateway"

  provisioner "local-exec" {
    command = "python import_api.py ${var.aws_access_key} ${var.aws_secret_key} ${aws_api_gateway_rest_api.ApiGateway.id}"
  }
}

resource "aws_api_gateway_deployment" "MyDemoDeployment" {
  rest_api_id = "${aws_api_gateway_rest_api.ApiGateway.id}"
  stage_name = "stage"

  # TODO Pull from environment or other configuration? This shoudl be generic for any gateway.
  variables = {
    discovery_host = "stage-edx-discovery.edx.org/api"
  }
}
