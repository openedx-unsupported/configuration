resource "aws_instance" "ec2_instance" {
    ami = "${var.ami_id}"
    vpc_security_group_ids = ["${split(",", var.security_group_id)}"]
    key_name = "${var.key_name}"
    subnet_id = "${var.subnet_id}"
    instance_type = "${var.instance_type}"
    count = "${var.number_of_instances}"
    tags {
        Name = "${var.instance_name}"
        Environment = "${var.environment}"
    }
}