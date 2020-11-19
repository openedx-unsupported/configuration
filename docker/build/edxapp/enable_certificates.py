import json

from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration,
    CertificateHtmlViewConfiguration,
)

# Enable self-generated certificates
config = CertificateGenerationConfiguration.objects.first()

if config is None or not config.enabled:
    CertificateGenerationConfiguration.objects.create(enabled=True)

# Add HTML Certificate configuration if none is set
config = CertificateHtmlViewConfiguration.objects.first()

config_schema_v0 = {
    "default": {
        "accomplishment_class_append": "accomplishment-certificate"
    },
    "honor": {
        "certificate_type": "",
        "certificate_title": "Certificate of Achievement"
    }
}

config_schema_v1 = {
    "default": {
        "accomplishment_class_append": "accomplishment-certificate",
        "logo_src": "",
        "logo_url": "",
        "company_verified_certificate_url": "",
        "company_privacy_url": "",
        "company_tos_url": "",
        "company_about_url": ""
    },
    "honor": {
        "certificate_type": "",
        "certificate_title": "Certificate of Achievement"
    }
}

old_config_schemas = [config_schema_v0]
current_config_schemas = config_schema_v1

if config is None or not config.enabled or json.loads(config.configuration) in old_config_schemas:
    CertificateHtmlViewConfiguration.objects.create(enabled=True, configuration=json.dumps(current_config_schemas))

quit()
