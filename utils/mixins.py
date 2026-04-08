# utils/mixins.py
from django.db.models import Exists, OuterRef, Value, BooleanField
from cources.models import Enrollment


class CourseEnrollmentAnnotationMixin:
    def annotate_is_enrolled(self, queryset, user):
        if user.is_authenticated and getattr(user, "role", None) == "student":
            return queryset.annotate(
                is_enrolled=Exists(
                    Enrollment.objects.filter(
                        student=user,
                        course=OuterRef("pk")
                    )
                )
            )
        return queryset.annotate(
            is_enrolled=Value(None, output_field=BooleanField())
        )