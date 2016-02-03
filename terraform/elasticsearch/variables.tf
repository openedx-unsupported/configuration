variable "aws_region" {
	default = "us-east-1"
}
variable "es_domain_name" { }
variable "es_instance_type" {
  default = "m3.medium.elasticsearch"
}
variable "es_zone_awareness" {
  default = false
}
variable "es_instance_count" {
  default = "1"
}
variable "es_ebs_volume_size" {
  default = "10"
}
variable "source_ip" { }

