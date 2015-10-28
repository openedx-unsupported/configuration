resource "aws_iam_policy" "topic_policy" {
    name = "${var.environment}-${var.deployment}-${var.service}-sender"
    path = "/"
    description = "Sender policy"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "sns:Publish"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sns_topic.build_requests.arn}"
    }
  ]
}
EOF
}

resource "aws_sqs_queue" "build_requests" {
	name = "${var.queue_name}"
	delay_seconds = "${var.queue_delay_seconds}"
	max_message_size = "${var.queue_max_message_size}"
	message_retention_seconds = "${var.queue_message_retention_seconds}"
	receive_wait_time_seconds = "${var.queue_receive_wait_time_seconds}"
}

resource "aws_sns_topic" "build_requests" {
	name = "user-updates-topic"
}

resource "aws_sns_topic_subscription" "build_requests_sqs_target" {
	topic_arn = "${aws_sns_topic.build_requests.arn}"
	protocol  = "sqs"
	endpoint  = "${aws_sqs_queue.build_requests.arn}"
}
