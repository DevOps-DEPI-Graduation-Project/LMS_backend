import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE cources_course ADD COLUMN instructor_id bigint NULL;")
        print("Added instructor_id column.")
    except Exception as e:
        print(f"Error adding column: {e}")
        
    try:
        cursor.execute("ALTER TABLE cources_course ADD CONSTRAINT cources_course_instructor_id_fk_users_instructor_id FOREIGN KEY (instructor_id) REFERENCES users_instructor(id);")
        print("Added foreign key constraint.")
    except Exception as e:
        print(f"Error adding foreign key: {e}")

