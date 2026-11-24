from django.contrib import admin
from .models import Student, AttendanceRecord, Unit, Timetable
import base64
import cv2
import face_recognition
import numpy as np
from django.utils.html import format_html
from django import forms

class StudentAdminForm(forms.ModelForm):
    photo_upload = forms.ImageField(required=False, label="Upload Student Portrait")

    class Meta:
        model = Student
        fields = ['name', 'reg_number', 'course', 'year']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ("display_photo_small", "name", "reg_number", "course", "year")
    readonly_fields = ("display_photo_large", "face_encoding")

    fieldsets = (
        ("Personal Information", {
            'fields': ('name', 'reg_number', 'course', 'year')
        }),
        ("Biometric Data", {
            'fields': ('photo_upload', 'display_photo_large', 'face_encoding'),
            'description': "Upload a clear portrait to automatically generate face encodings."
        }),
    )

    def save_model(self, request, obj, form, change):
        photo = form.cleaned_data.get('photo_upload')
        if photo:
            # 1. Store raw photo bytes
            photo_bytes = photo.read()
            obj.photo = photo_bytes

            # 2. Generate face encoding
            try:
                # Need to reset pointer after read()
                photo.seek(0)
                image = face_recognition.load_image_file(photo)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    obj.face_encoding = encodings[0].tobytes()
            except Exception as e:
                self.message_user(request, f"Error encoding face: {e}", level='ERROR')

        super().save_model(request, obj, form, change)

    def display_photo_large(self, obj):
        if obj.photo:
            encoded = base64.b64encode(obj.photo).decode('utf-8')
            return format_html('<img src="data:image/png;base64,{}" style="max-width: 300px; border-radius: 10px;" />', encoded)
        return "No Portrait Uploaded"
    display_photo_large.short_description = "Current Portrait"

    def display_photo_small(self, obj):
        if obj.photo:
            encoded = base64.b64encode(obj.photo).decode('utf-8')
            return format_html('<img src="data:image/png;base64,{}" style="width: 45px; height: 45px; border-radius: 50%; object-fit: cover;" />', encoded)
        return "No Photo"
    display_photo_small.short_description = "Photo"

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "hours_per_week")

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("unit", "day", "start_time", "end_time", "venue")
    list_filter = ("day", "venue", "unit")

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "unit", "date", "time", "venue", "colored_status")
    list_filter = ("date", "status", "unit", "venue")

    def colored_status(self, obj):
        return format_html('<span class="status-present">{}</span>', obj.status) if obj.status == "Present" else obj.status
    colored_status.short_description = "Status"

admin.site.site_header = "👤 Face Attendance Administration"
