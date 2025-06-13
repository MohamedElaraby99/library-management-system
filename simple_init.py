#!/usr/bin/env python3
from app import app, db
from models import User

def create_sample_data():
    with app.app_context():
        system_admin = User.query.filter_by(username="araby").first()
        if not system_admin:
            system_admin = User(username="araby", role="admin", is_system=True)
            system_admin.set_password("92321066")
            db.session.add(system_admin)
            print("تم إنشاء المستخدم الافتراضي المخفي: araby")
        
        db.session.commit()
        print("تم إنشاء البيانات الأولية بنجاح!")

if __name__ == "__main__":
    create_sample_data() 