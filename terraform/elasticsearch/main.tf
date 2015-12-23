resource "aws_elasticsearch_domain" "es" {
    domain_name = "${var.es_domain_name}"
    advanced_options {
        "rest.action.multi.allow_explicit_index" = true
    }
    cluster_config {
        instance_type = "${var.es_instance_type}"
        instance_count = "${var.es_instance_count}"
        zone_awareness_enabled = true
    }
    ebs_options {
        ebs_enabled = true
        volume_size = "${var.es_ebs_volume_size}"
    }
    access_policies = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "es:*",
            "Principal": "*",
            "Effect": "Allow",
            "Condition": {
                "IpAddress": {"aws:SourceIp": ["${var.source_ip}"]}
            }
        }
    ]
}
EOF

    snapshot_options {
        automated_snapshot_start_hour = 0 
    }
}

output "endpoint" {
    value = "${endpoint}"
}
