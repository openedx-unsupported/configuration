
# Configure the AWS Provider
provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "us-east-1"
}


# pipeline-provision infrastructure
resource "aws_sqs_queue" "edx-pipeline-provision" {
	name = "${var.queue_name_pipeline}"
	delay_seconds = "${var.queue_delay_seconds}"
	max_message_size = "${var.queue_max_message_size}"
	message_retention_seconds = "${var.queue_message_retention_seconds}"
	receive_wait_time_seconds = "${var.queue_receive_wait_time_seconds}"
}

resource "aws_sns_topic" "edx-pipeline-provision" {
  name = "edx-pipeline-provision-topic"
}

resource "aws_sns_topic_subscription" "edx-pipeline-provision_sqs_target" {
  topic_arn = "${aws_sns_topic.edx-pipeline-provision.arn}"
  protocol  = "sqs"
  endpoint  = "${aws_sqs_queue.edx-pipeline-provision.arn}"
}



# pipeline-sitespeed infrastructure
resource "aws_sqs_queue" "edx-pipeline-sitespeed" {
  name = "${var.queue_name_sitespeed}"
  delay_seconds = "${var.queue_delay_seconds}"
  max_message_size = "${var.queue_max_message_size}"
  message_retention_seconds = "${var.queue_message_retention_seconds}"
  receive_wait_time_seconds = "${var.queue_receive_wait_time_seconds}"
}

resource "aws_sns_topic" "edx-pipeline-sitespeed" {
  name = "edx-pipeline-sitespeed-topic"
}

resource "aws_sns_topic_subscription" "edx-pipeline-sitespeed_sqs_target" {
  topic_arn = "${aws_sns_topic.edx-pipeline-sitespeed.arn}"
  protocol  = "sqs"
  endpoint  = "${aws_sqs_queue.edx-pipeline-sitespeed.arn}"
}


# Create IAM policy, user
resource "aws_iam_user" "build_pipeline_user" {
    name = "build_pipeline_user"
}

resource "aws_iam_access_key" "build_pipeline_user_key" {
    user = "${aws_iam_user.build_pipeline_user.name}"
}

resource "aws_iam_user_policy" "sns_publish_policy" {
    name = "${var.environment}-${var.deployment}-${var.service}-sender"
    user = "${aws_iam_user.build_pipeline_user.name}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "sns:Publish"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sns_topic.edx-pipeline-provision.arn}"
    },
    {
      "Action": [
        "sns:Publish"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sns_topic.edx-pipeline-sitespeed.arn}"
    }
  ]
}
EOF
}

