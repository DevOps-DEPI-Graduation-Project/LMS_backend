from urllib import request

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

    # Get file extension dynamically
    # extension = serializers.ReadOnlyField(source="file_extension")

    # Human readable file size
    # file_size = serializers.SerializerMethodField()


    file = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()


    class Meta:
        model = Material
        fields = [
            "course",
            "slug",
            "Material_Name",
            # "material_type",
            "file",
            # "description",
            # "extension",
            "file_size",
            # "created_at",
        ]

        read_only_fields = ["slug"]

    def get_file(self, obj):
        request = self.context.get("request")
        if obj.file:
            file_url = obj.file.url
            return request.build_absolute_uri(file_url) if request else file_url
        return None

    def get_file_size(self, obj):
        try:
            if obj.file:
                return f"{round(obj.file.size / (1024 * 1024), 2)} MB"
            return None
        except Exception:
            return "Unknown"