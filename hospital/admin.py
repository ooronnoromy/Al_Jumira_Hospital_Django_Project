from django.contrib import admin
from django.apps import apps
from django.db import models as django_models

SENSITIVE_FIELD_NAMES = {"password"}


def _model_admin_for(model):
    """Build a useful, safe default admin view for a hospital model."""

    concrete_fields = [
        field
        for field in model._meta.concrete_fields
        if field.name not in SENSITIVE_FIELD_NAMES
    ]
    list_display = tuple(field.name for field in concrete_fields[:6])
    search_fields = tuple(
        field.name
        for field in concrete_fields
        if isinstance(field, (django_models.CharField, django_models.TextField))
        and not field.name.endswith("_json")
    )[:4]

    return type(
        f"{model.__name__}Admin",
        (admin.ModelAdmin,),
        {
            "list_display": list_display,
            "search_fields": search_fields,
            "list_per_page": 50,
        },
    )


# Register every database-backed model in the hospital app. Keeping this
# automatic also makes newly added hospital tables appear in Django Admin.
for hospital_model in apps.get_app_config("hospital").get_models():
    if not admin.site.is_registered(hospital_model):
        admin.site.register(hospital_model, _model_admin_for(hospital_model))
