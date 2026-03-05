from django.shortcuts import render

# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import Course
from .serializer import CourseCreateSerializer


class CourseCreateAPIView(CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = serializer.save()

        return Response(
            {
                "message": "Course created successfully",
                "status": status.HTTP_201_CREATED,
                "data": CourseCreateSerializer(course).data
            },
            status=status.HTTP_201_CREATED
        )