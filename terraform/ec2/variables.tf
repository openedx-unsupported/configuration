variable "instance_type" {
	description = "Type of instance"
	default = "t2.micro"
}

variable "key_name" {
	description = "SSH keypair you've created"
}

variable "security_group_id" {
	description = "Security Group you've created"
}

variable "subnet_id" {
  description = "The VPC subnet the instance(s) will go in"
}

variable "ami_id" {
  description = "AMI use to spinup this EC2 Instance"
}

variable "number_of_instances" {
  default = 1
}

variable "instance_name" {
  default = "sandbox"
}

variable "environment" {
  default = "dev"
}

