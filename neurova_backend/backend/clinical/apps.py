from django.apps import AppConfig

class ClinicalConfig(AppConfig):
    name = "backend.clinical"

    def ready(self):
        # Phase E: register submodule models
        from backend.clinical.policies import models  # noqa
        from backend.clinical.signoff import models  # noqa
