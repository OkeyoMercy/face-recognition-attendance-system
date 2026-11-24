from django.db import models

class Unit(models.Model):
    code = models.CharField(max_length=20, unique=True) # e.g., CIR 101
    name = models.CharField(max_length=100) # e.g., Discrete Structures
    hours_per_week = models.IntegerField(default=6)

    def __str__(self):
        return f"{self.code}: {self.name}"

class Timetable(models.Model):
    DAYS = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    day = models.CharField(max_length=15, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=50) # TB2, NL5, LAB3

    def __str__(self):
        return f"{self.unit.code} - {self.day} ({self.venue})"

class Student(models.Model):
    name = models.CharField(max_length=100)
    reg_number = models.CharField(max_length=50, unique=True)
    course = models.CharField(max_length=100, default="BSc. Computer Science")
    year = models.IntegerField(default=1)
    face_encoding = models.BinaryField(null=True, blank=True)
    photo = models.BinaryField(null=True, blank=True) # Store actual image data

    def __str__(self):
        return f"{self.name} ({self.reg_number})"

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True)
    venue = models.CharField(max_length=50, null=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default="Present")

    def __str__(self):
        return f"{self.student.name} - {self.unit.code} - {self.date}"
