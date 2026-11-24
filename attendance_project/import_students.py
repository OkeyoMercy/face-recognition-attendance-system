import os
import django
import cv2
import face_recognition
import numpy as np

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from attendance_app.models import Student

def import_from_folder(folder_path):
    """
    Expects a folder where images are named 'RegistrationNumber.jpg' or 'RegistrationNumber.png'
    Example: 'CS1-001.jpg'
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"📁 Created folder: {folder_path}. Please place student photos there and run again.")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            reg_number = os.path.splitext(filename)[0]

            # Skip if already exists
            if Student.objects.filter(reg_number=reg_number).exists():
                print(f"⏩ Student {reg_number} already exists. Skipping.")
                continue

            image_path = os.path.join(folder_path, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                # Resize for consistency
                image = cv2.resize(image, (640, 480))
                encodings = face_recognition.face_encodings(image)

                if len(encodings) == 1:
                    encoding_bytes = encodings[0].tobytes()
                    # We'll use the reg_number as a placeholder name for now
                    # You can change the names manually in the Admin later
                    Student.objects.create(
                        name=f"Student {reg_number}",
                        reg_number=reg_number,
                        course="BSc. Computer Science",
                        year=1,
                        face_encoding=encoding_bytes
                    )
                    print(f"✅ Registered: {reg_number}")
                else:
                    print(f"❌ Error for {filename}: Ensure exactly ONE face is visible.")
            except Exception as e:
                print(f"❌ Failed to process {filename}: {str(e)}")

if __name__ == "__main__":
    print("--- Bulk Student Import ---")
    import_from_folder("student_photos")
