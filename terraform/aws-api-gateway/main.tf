provider "aws" {
    region = "${var.aws_region}"
}

resource "aws_api_gateway_rest_api" "api" {
  name = "${var.api_name}"
  description = "${var.api_description}"
}

resource "aws_api_gateway_resource" "res" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  parent_id = "${aws_api_gateway_rest_api.api.root_resource_id}"
  path_part = "${var.resource_name}"
}

resource "aws_api_gateway_method" "resource_method" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  resource_id = "${aws_api_gateway_resource.res.id}"
  http_method = "${var.http_method}"
  authorization = "${var.authorization}"
}

resource "aws_api_gateway_integration" "method_request" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  resource_id = "${aws_api_gateway_resource.res.id}"
  http_method = "${aws_api_gateway_method.resource_method.http_method}"
  type = "HTTP"
  uri = "${var.backend_api_url}"
  integration_http_method = "${var.integration_http_method}"
}

resource "aws_api_gateway_method_response" "method_response" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  resource_id = "${aws_api_gateway_resource.res.id}"
  http_method = "${aws_api_gateway_method.resource_method.http_method}"
  status_code = "200"
   response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "integration_request" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  resource_id = "${aws_api_gateway_resource.res.id}"
  http_method = "${aws_api_gateway_method.resource_method.http_method}"
  status_code = "${aws_api_gateway_method_response.method_response.status_code}"
  selection_pattern = "${var.api_selection_pattern}"
}

resource "aws_api_gateway_deployment" "api_gateway_deployment" {
  depends_on = ["aws_api_gateway_integration.method_request"]

  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  stage_name  = "${var.api_deployment_stage_name}"
}