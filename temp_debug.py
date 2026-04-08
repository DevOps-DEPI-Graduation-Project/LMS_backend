from cources.models import Package, Course, Enrollment
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, FloatField, Exists, OuterRef, Value, BooleanField
from django.db.models.functions import Coalesce

user = get_user_model().objects.filter(role='student').first()
print('user', user)

qs = Course.objects.annotate(
    avg_rating=Coalesce(Avg('ratings__rate'), 0.0, output_field=FloatField()),
    ratings_count=Count('ratings'),
    students_count=Count('enrollments', distinct=True)
)
if user:
    qs = qs.annotate(
        is_enrolled=Exists(
            Enrollment.objects.filter(
                student=user,
                course=OuterRef('pk')
            )
        )
    )

if qs.exists():
    first = qs.first()
    print('sample course fields', list(first.__dict__.keys()), getattr(first, 'is_enrolled', None))
else:
    print('sample course queryset empty')

pkg = Package.objects.prefetch_related(
    __import__('django.db.models').db.models.Prefetch('courses', queryset=qs)
).first()
print('pkg', pkg)

if pkg and pkg.courses.all().exists():
    course = pkg.courses.all()[0]
    print('course from package', course.slug, getattr(course, 'is_enrolled', None))
else:
    print('no package or no courses')
