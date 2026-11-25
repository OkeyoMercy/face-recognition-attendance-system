from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import datetime
from .models import Student, AttendanceRecord, Timetable, Unit
try:
    import face_recognition
    import numpy as np
    import cv2
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    face_recognition = None
    np = None
    cv2 = None
    FACE_RECOGNITION_AVAILABLE = False
import base64
import json
import csv

# Module-level encoding cache
_encoding_cache = None

def _get_known_encodings():
    global _encoding_cache
    if _encoding_cache is None:
        encodings, students = [], []
        for s in Student.objects.exclude(face_encoding__isnull=True):
            enc = np.frombuffer(s.face_encoding, dtype=np.float64)
            if len(enc) == 128:
                encodings.append(enc)
                students.append(s)
        _encoding_cache = (encodings, students)
    return _encoding_cache

# --- VIEWS ---

def login_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'attendance_app/login.html', {'form': {'errors': True}})
    return render(request, 'attendance_app/login.html')

@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('login')

def admin_login_redirect(request):
    auth_logout(request)
    return redirect('/admin/login/?next=/admin/')

@login_required(login_url='login')
def dashboard(request):
    total_students = Student.objects.count()
    today = datetime.date.today()
    today_records = AttendanceRecord.objects.filter(date=today)
    total_present_today = today_records.count()
    total_absent_today = max(0, total_students - total_present_today)

    present_percentage = (total_present_today / total_students * 100) if total_students > 0 else 0
    total_sessions = AttendanceRecord.objects.values('date').distinct().count()
    recent_records = AttendanceRecord.objects.select_related('student', 'unit').order_by('-date', '-time')[:10]

    return render(request, 'attendance_app/dashboard.html', {
        'total_students': total_students,
        'total_present': total_present_today,
        'total_absent': total_absent_today,
        'present_percentage': round(present_percentage, 2),
        'total_sessions': total_sessions,
        'recent_records': recent_records,
        'today': today.strftime("%d %b %Y, %A")
    })


@login_required(login_url='login')
def process_scan(request):
    if not FACE_RECOGNITION_AVAILABLE:
        return JsonResponse({
            "status": "error",
            "message": "Face recognition is disabled in this online demo. Please use the local version for scanning."
        })
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            unit_id = data.get('course')

            if not image_data or not unit_id:
                return JsonResponse({"status": "error", "message": "Missing image or unit selection"})

            unit = Unit.objects.filter(id=unit_id).first()
            if not unit:
                return JsonResponse({"status": "error", "message": "Invalid unit selected."})

            # Process Image
            header, encoded = image_data.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Resize for faster processing
                # Process image at original camera resolution
            rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            if not face_locations:
                return JsonResponse({"status": "error", "message": "No face detected in frame."})

            encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            known_encodings, known_students = _get_known_encodings()

            results = []
            for encoding in encodings:
                distances = face_recognition.face_distance(known_encodings, encoding)
                if len(distances) > 0:
                    best_match = np.argmin(distances)
                    # Matching CLI tolerance of 0.45
                    if distances[best_match] < 0.45:
                        student = known_students[best_match]

                        today = datetime.date.today()
                        record, created = AttendanceRecord.objects.get_or_create(
                            student=student, unit=unit, date=today,
                            defaults={'venue': "SCANNER", 'status': 'Present'}
                        )

                        if created:
                            results.append(f"✅ {student.name} marked present!")
                        else:
                            results.append(f"ℹ️ {student.name} already recorded.")
                    else:
                        results.append("❓ Face detected but no matching profile found.")

            if not results:
                return JsonResponse({"status": "error", "message": "No matches found."})

            return JsonResponse({"status": "success", "message": " | ".join(results)})
        except Exception as e:
            import traceback
            print("FACE SCAN ERROR:", repr(e))
            traceback.print_exc()

            return JsonResponse({
                "status": "error",
                "message": "Processing error. Please check the server terminal."
            })
    return JsonResponse({"status": "error", "message": "Invalid method"})

@login_required(login_url='login')
def scanner(request):
    units = Unit.objects.all()
    return render(request, 'attendance_app/scanner.html', {'units': units})

@login_required(login_url='login')
def tracking(request):
    records = AttendanceRecord.objects.select_related('student', 'unit').all().order_by('-date', '-time')

    # Filtering logic
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    unit_id = request.GET.get('course') # This is the unit ID from dropdown

    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if unit_id:
        records = records.filter(unit_id=unit_id)

    units = Unit.objects.all()
    return render(request, 'attendance_app/tracking.html', {
        'records': records,
        'units': units
    })

@login_required(login_url='login')
def export_csv(request):
    records = AttendanceRecord.objects.select_related('student', 'unit').all().order_by('-date', '-time')

    # Filtering logic
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    unit_id = request.GET.get('course')

    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if unit_id:
        records = records.filter(unit_id=unit_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    writer = csv.writer(response)
    writer.writerow(['Student', 'Reg No', 'Unit', 'Venue', 'Date', 'Time'])
    for r in records:
        unit_code = r.unit.code if r.unit else "N/A"
        writer.writerow([r.student.name, r.student.reg_number, unit_code, r.venue, r.date, r.time])
    return response

def forgot_password(request):
    return render(request, 'attendance_app/forgot_password.html')

@login_required(login_url='login')
def register_student(request):
    if request.method == 'POST':
        if not FACE_RECOGNITION_AVAILABLE:
            messages.error(request, "Photo registration is disabled in this online demo. Please use the local version for face recognition.")
            return render(request, 'attendance_app/register_student.html')
        name = request.POST.get('name')
        reg_number = request.POST.get('reg_number')
        course = request.POST.get('course')
        photo_file = request.FILES.get('photo')

        if photo_file and photo_file.size > 5 * 1024 * 1024:
            messages.error(request, "Photo size must not exceed 5 MB.")
            return render(request, 'attendance_app/register_student.html')

        if not all([name, reg_number, course, photo_file]):
            messages.error(request, "All fields are required.")
            return render(request, 'attendance_app/register_student.html')

        try:
            # Read photo data
            photo_data = photo_file.read()

            # Process for face encoding
            nparr = np.frombuffer(photo_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                messages.error(request, "Invalid image file. Please upload a valid photo.")
                return render(request, 'attendance_app/register_student.html')

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_img)

            if len(encodings) == 0:
                messages.error(request, "No face detected. Please upload a clear photo.")
                return render(request, 'attendance_app/register_student.html')

            if len(encodings) > 1:
                messages.error(request, "Multiple faces detected. Please upload a photo showing only one person.")
                return render(request, 'attendance_app/register_student.html')

            face_encoding = encodings[0].tobytes()

            # Save Student
            student, created = Student.objects.update_or_create(
                reg_number=reg_number,
                defaults={
                    'name': name,
                    'course': course,
                    'photo': photo_data,
                    'face_encoding': face_encoding
                }
            )

            if created:
                messages.success(request, f"Student {name} registered successfully!")
            else:
                messages.success(request, f"Student {name} updated successfully!")

            return redirect('register_student')

        except Exception:
            messages.error(request, "Registration failed. Please check the photo and try again.")

    return render(request, 'attendance_app/register_student.html')
def welcome(request):
    return render(request, 'welcome.html')
def demo(request):
    return render(request, 'attendance_app/demo.html')
def demo(request):
    return render(request, 'attendance_app/demo.html')
