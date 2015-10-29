variable "environment" {}
variable "deployment" {}
variable "service" {}

variable "queue_name" {
	 default = "default-queue"
}
variable "queue_delay_seconds" {}
variable "queue_max_message_size" {}
variable "queue_message_retention_seconds" {}
variable "queue_receive_wait_time_seconds" {}

variable "aws_access_key" {}
variable "aws_secret_key" {}
