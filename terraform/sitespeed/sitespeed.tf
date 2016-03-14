# Configure the AWS Provider
provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  region = "${var.aws_region}"
}

# Create a new IAM user
resource "aws_iam_user" "build_pipeline_user" {
  name = "build_pipeline_user"
}

# Create IAM access key for the new user
resource "aws_iam_access_key" "build_pipeline_user_key" {
  user = "${aws_iam_user.build_pipeline_user.name}"
}

# Create the SNS topics
resource "aws_sns_topic" "provision-topic" {
  name = "edx-pipeline-provision-topic"
}
resource "aws_sns_topic" "sitespeed-topic" {
  name = "edx-pipeline-sitespeed-topic"
}

# Create the SQS queues, including giving permission to
# the SNS topics to send messages to the queue
resource "aws_sqs_queue" "provision-queue" {
  name = "${var.provision_queue_name}"
  delay_seconds = "${var.queue_delay_seconds}"
  max_message_size = "${var.queue_max_message_size}"
  message_retention_seconds = "${var.queue_message_retention_seconds}"
  receive_wait_time_seconds = "${var.queue_receive_wait_time_seconds}"
  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "SQS:SendMessage",
      "Principal": "*",
      "Resource": "${format("arn:aws:sqs:%s:%s:%s", var.aws_region, var.aws_account_id, var.provision_queue_name)}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_sns_topic.provision-topic.arn}"
        }
      }
    }
  ]
}
EOF
}

resource "aws_sqs_queue" "sitespeed-queue" {
  name = "${var.sitespeed_queue_name}"
  delay_seconds = "${var.queue_delay_seconds}"
  max_message_size = "${var.queue_max_message_size}"
  message_retention_seconds = "${var.queue_message_retention_seconds}"
  receive_wait_time_seconds = "${var.queue_receive_wait_time_seconds}"
  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "SQS:SendMessage",
      "Principal": "*",
      "Resource": "${format("arn:aws:sqs:%s:%s:%s", var.aws_region, var.aws_account_id, var.sitespeed_queue_name)}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_sns_topic.sitespeed-topic.arn}"
        }
      }
    }
  ]
}
EOF
}

# Subscribe the SQS queues to the SNS topics
resource "aws_sns_topic_subscription" "provision-subscription" {
  topic_arn = "${aws_sns_topic.provision-topic.arn}"
  protocol  = "sqs"
  endpoint  = "${aws_sqs_queue.provision-queue.arn}"
}
resource "aws_sns_topic_subscription" "sitespeed-subscription" {
  topic_arn = "${aws_sns_topic.sitespeed-topic.arn}"
  protocol  = "sqs"
  endpoint  = "${aws_sqs_queue.sitespeed-queue.arn}"
}

# Allow the IAM user to publish to the SNS topics
# and to read and delete from the SQS queues.
# Jenkins and the build-trigger heroku app will be
# configured to use its key.
resource "aws_iam_user_policy" "user-pipeline-policy" {
  name = "${var.environment}-${var.deployment}-${var.service}-sender"
  user = "${aws_iam_user.build_pipeline_user.name}"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "${aws_sns_topic.provision-topic.arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "${aws_sqs_queue.provision-queue.arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "${aws_sns_topic.sitespeed-topic.arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "${aws_sqs_queue.sitespeed-queue.arn}"
    }
  ]
}
EOF
}

# Output the AWS key and secret for the new user to the console.
# Note that it will also be available in the terraform.tfstate file.
output "key" {
    value = "${aws_iam_access_key.build_pipeline_user_key.id}"
}
output "secret" {
    value = "${aws_iam_access_key.build_pipeline_user_key.secret}"
}
