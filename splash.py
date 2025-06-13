import tkinter as tk
from tkinter import ttk
import time
import threading

def show_splash():
    """عرض شاشة البداية"""
    # إنشاء النافذة
    root = tk.Tk()
    root.title("نظام إدارة المكتبة")
    
    # تعيين حجم النافذة
    window_width = 400
    window_height = 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # إزالة إطار النافذة
    root.overrideredirect(True)
    
    # تعيين الخلفية
    root.configure(bg='#1e3c72')
    
    # إضافة الشعار
    logo_label = tk.Label(
        root,
        text="نظام إدارة المكتبة",
        font=("Arial", 24, "bold"),
        fg="white",
        bg='#1e3c72'
    )
    logo_label.pack(pady=20)
    
    # إضافة شريط التقدم
    progress = ttk.Progressbar(
        root,
        length=300,
        mode='determinate'
    )
    progress.pack(pady=20)
    
    # إضافة النص
    text_label = tk.Label(
        root,
        text="جاري تحميل النظام...",
        font=("Arial", 12),
        fg="white",
        bg='#1e3c72'
    )
    text_label.pack(pady=10)
    
    # خطوات التحميل
    steps = [
        "جاري تهيئة النظام...",
        "جاري تحميل قاعدة البيانات...",
        "جاري تحميل الواجهة...",
        "جاري التحقق من الصلاحيات...",
        "جاري فتح المتصفح..."
    ]
    
    def update_progress():
        """تحديث شريط التقدم والنص"""
        for i, step in enumerate(steps):
            progress['value'] = (i + 1) * 20
            text_label['text'] = step
            root.update()
            time.sleep(0.5)
        root.destroy()
    
    # بدء التحديث في خيط منفصل
    threading.Thread(target=update_progress).start()
    
    # تشغيل النافذة
    root.mainloop() 