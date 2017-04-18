provider "aws" {
    region = "${var.aws_region}"
}

// Setup your S3 Bucket
resource "aws_s3_bucket" "cdn_bucket" {
  bucket = "${var.bucket_name}"
  acl = "public-read"
  policy = <<POLICY
{
  "Version":"2012-10-17",
  "Statement":[{
    "Sid":"PublicReadForGetBucketObjects",
      "Effect":"Allow",
      "Principal": "*",
      "Action":"s3:GetObject",
      "Resource":["arn:aws:s3:::${var.bucket_name}/*"
      ]
    }
  ]
}
POLICY

}

// Setup the CloudFront Distribution
resource "aws_cloudfront_distribution" "cloudfront_distribution" {
  origin {
    domain_name = "${var.bucket_name}.s3.amazonaws.com"
    origin_id = "S3-${var.bucket_name}"
    s3_origin_config {}
  }
  enabled = true
  //aliases = ["mytestapi.com", "www.mytestapi.com"]
  price_class = "${var.price_class}"
  default_cache_behavior {
    allowed_methods = [ "DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT" ]
    cached_methods = [ "GET", "HEAD" ]
    target_origin_id = "S3-${var.bucket_name}"
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
    viewer_protocol_policy = "allow-all"
    min_ttl = 0
    default_ttl = 3600
    max_ttl = 86400
  }
  retain_on_delete = "${var.retain_on_delete}"
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

//Add Root Route53 Records
resource "aws_route53_record" "main_record" {
  zone_id = "${var.hosted_zone_id}"
  name = "${var.route53_record_name}.${var.domain_name}"
  type = "A"

  alias {
    name = "${aws_cloudfront_distribution.cloudfront_distribution.domain_name}"
    zone_id = "${var.alias_zone_id}"
    evaluate_target_health = false
  }
}

