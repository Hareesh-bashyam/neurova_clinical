from django.core.exceptions import ValidationError

class ImmutableModelMixin:
    immutable_fields = None  # set list if needed

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Immutable record: updates are not allowed.")
        return super().save(*args, **kwargs)

