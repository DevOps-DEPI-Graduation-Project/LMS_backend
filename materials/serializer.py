from rest_framework import serializers
from .models import Material

class MaterialSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for converting Material objects
    to JSON responses for the API.
    """

    course = serializers.SlugRelatedField(
        queryset=Material._meta.get_field('course').remote_field.model.objects.all(),
        slug_field='slug'
    )

    file_size = serializers.SerializerMethodField()

    file = serializers.FileField(required=True)

    class Meta:
        model = Material
        fields = [
            "course",
            "slug",
            "Material_Name",
            "file",
            "file_size",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]

    def get_file_size(self, obj):
        try:
            if obj.file:
                return f"{round(obj.file.size / (1024 * 1024), 2)} MB"
            return None
        except Exception:
            return "Unknown"


class CourseMaterialCreateSerializer(MaterialSerializer):
    """
    Serializer for creating/updating materials within a course scope.
    The course is handled by the URL, so it's read-only here.
    """
    course = serializers.SlugRelatedField(read_only=True, slug_field='slug')

    class Meta(MaterialSerializer.Meta):
        read_only_fields = MaterialSerializer.Meta.read_only_fields + ["course"]