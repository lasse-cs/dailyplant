from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage as DjangoManifestStaticFilesStorage,
)


class ManifestStaticFilesStorage(DjangoManifestStaticFilesStorage):
    support_js_module_import_aggregation = True
