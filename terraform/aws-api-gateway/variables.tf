variable aws_region {
	default = "us-east-1"
}

variable api_name {
	description = "Name that you want to assign to your api"
}

variable api_description {
	description = "Description that you want to give to your api"
}

variable resource_name {
	description = "Name that you want to assign to your resource"
}

variable http_method {
    default = "GET"
}

variable authorization {
	default = "NONE"
}

variable backend_api_url {
	description = "URL of your backend api"
}

variable integration_http_method {
	default = "GET"
}
variable api_selection_pattern {
	
}

variable api_deployment_stage_name {
	
}
