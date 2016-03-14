variable "environment" {}
variable "deployment" {}
variable "service" {}

variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_account_id" {}
variable "aws_region" {
	default = "us-east-1"
}

variable "provision_queue_name" {
	default = "edx-pipeline-provision-queue"
}
variable "sitespeed_queue_name" {
	default = "edx-pipeline-sitespeed-queue"
}

variable "queue_delay_seconds" {
	default = 0
}
variable "queue_max_message_size" {
	default = 262144
}
variable "queue_message_retention_seconds" {
	default = 345600
}
variable "queue_receive_wait_time_seconds" {
	default = 5
}
