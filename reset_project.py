import os
import shutil
import django
from django.conf import settings
from django.db import connection, ProgrammingError

# إعداد بيئة جانغو لاستخدام الاتصال
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redivio_project.settings')
django.setup()

def clean_project():
    print("🚀 Starting Full Project Cleanup (PostgreSQL/NeonDB Edition)...")

    # 1. حذف الـ Schema العامة في قاعدة البيانات (Reset DB)
    # هذا يعادل حذف ملف sqlite ولكن لقواعد البيانات الكبيرة
    with connection.cursor() as cursor:
        try:
            print("⏳ Dropping 'public' schema from Database...")
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;") # صلاحيات
            print("✅ Database wiped successfully (Public schema recreated).")
        except Exception as e:
            print(f"⚠️ Error cleaning DB (might be already empty): {e}")

    # 2. حذف ملفات الميجريشن المحلية
    root_dir = os.getcwd()
    migration_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if dirpath.endswith("migrations"):
            for filename in filenames:
                if filename != "__init__.py" and filename.endswith(".py"):
                    file_path = os.path.join(dirpath, filename)
                    try:
                        os.remove(file_path)
                        migration_count += 1
                    except Exception as e:
                        print(f"❌ Error deleting {file_path}: {e}")
            
            # تنظيف الكاش
            pycache_path = os.path.join(dirpath, "__pycache__")
            if os.path.exists(pycache_path):
                shutil.rmtree(pycache_path, ignore_errors=True)

    print(f"✅ Deleted {migration_count} old migration files.")
    print("\n✨ Cleanup Complete! Now run the following commands:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate_schemas --shared")
    print("3. python manage.py shell (create tenant)")

if __name__ == "__main__":
    clean_project()