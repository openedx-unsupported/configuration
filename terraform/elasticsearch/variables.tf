variable "aws_region" {
	default = "us-east-1"
}
variable "es_domain_name" { }
variable "es_instance_type" {
  default = "m3.large.elasticsearch"
}
variable "es_instance_count" {
  default = "5"
}
variable "es_ebs_volume_size" {
  default = "100"
}
variable "source_ip" { }

