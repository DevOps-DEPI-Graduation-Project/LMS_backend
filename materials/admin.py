from django.contrib import admin
from .models import Material

# Register your models here.

# @admin.register(Material)
# class MaterialAdmin(admin.ModelAdmin):
#     list_display = ('title', 'course', 'material_type', 'file_extension', 'created_at')
#     list_filter = ('material_type', 'course', 'created_at')
#     search_fields = ('title', 'course__title', 'description')
#     readonly_fields = ('slug', 'created_at', 'updated_at')
#     fieldsets = (
#         ('General Information', {
#             'fields': ('title', 'slug', 'course', 'material_type')
#         }),
#         ('File & Details', {
#             'fields': ('file', 'description')
#         }),
#         ('System Metadata', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

#     def file_extension(self, obj):
#         return obj.file_extension or "—"
#     file_extension.short_description = "Extension"


from django.contrib import admin
from .models import Material

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Material model.
    Synchronized with the new field names (Material_Name, slug, course).
    """
    
    # Displaying existing fields only 
    list_display = ("Material_Name", "course", "slug")
    
    # Filtering by the related course 
    list_filter = ("course",)
    
    # Search by material name 
    search_fields = ("Material_Name", "slug")
    
    # Auto-filling the slug is handled in the model save method 
    # but we can keep it readonly in admin for safety
    readonly_fields = ("slug",)