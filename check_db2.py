import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES;")
    tables = [t[0] for t in cursor.fetchall() if 'cources' in t[0]]
    for table in tables:
        print(f"Table: {table}")
        cursor.execute(f"SHOW COLUMNS FROM {table};")
        for col in cursor.fetchall():
            print("  ", col)
