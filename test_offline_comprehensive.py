#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار شامل للتأكد من توفر جميع الصفحات والميزات أوفلاين
Comprehensive test to ensure all pages and features are available offline
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class OfflineComprehensiveTest:
    def __init__(self):
        self.results = {
            'test_time': datetime.now().isoformat(),
            'status': 'starting',
            'tests': {},
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء الاختبار الشامل للصفحات الأوفلاين...")
        
        try:
            # اختبار الملفات الأساسية
            self.test_core_files()
            
            # اختبار ملفات JavaScript
            self.test_javascript_files()
            
            # اختبار ملفات CSS
            self.test_css_files()
            
            # اختبار Service Worker
            self.test_service_worker()
            
            # اختبار قوالب HTML
            self.test_html_templates()
            
            # اختبار API endpoints
            self.test_api_endpoints()
            
            # اختبار التكامل
            self.test_integration()
            
            # إنشاء التقرير النهائي
            self.generate_report()
            
            self.results['status'] = 'completed'
            
        except Exception as e:
            self.results['status'] = 'failed'
            self.results['errors'].append(f"Critical error: {str(e)}")
            print(f"❌ خطأ خطير: {e}")
        
        return self.results
    
    def test_core_files(self):
        """اختبار الملفات الأساسية"""
        print("📁 اختبار الملفات الأساسية...")
        
        core_files = [
            'app.py',
            'models.py', 
            'forms.py',
            'config.py',
            'requirements.txt'
        ]
        
        test_results = []
        
        for file_path in core_files:
            if os.path.exists(file_path):
                test_results.append({
                    'file': file_path,
                    'status': 'exists',
                    'size': os.path.getsize(file_path)
                })
                print(f"✅ {file_path} موجود")
            else:
                test_results.append({
                    'file': file_path,
                    'status': 'missing',
                    'size': 0
                })
                print(f"❌ {file_path} مفقود")
                self.results['errors'].append(f"Core file missing: {file_path}")
        
        self.results['tests']['core_files'] = test_results
    
    def test_javascript_files(self):
        """اختبار ملفات JavaScript الأوفلاين"""
        print("📄 اختبار ملفات JavaScript...")
        
        js_files = {
            'static/js/service-worker.js': {
                'required_content': ['STATIC_FILES', 'API_URLS', 'fetch'],
                'min_size': 5000
            },
            'static/js/db-manager.js': {
                'required_content': ['DBManager', 'IndexedDB', 'getProducts'],
                'min_size': 15000
            },
            'static/js/sync-manager.js': {
                'required_content': ['SyncManager', 'performSync', 'online'],
                'min_size': 8000
            },
            'static/js/offline-handler.js': {
                'required_content': ['OfflineHandler', 'enhanceForOffline', 'setupOfflineStatusBar'],
                'min_size': 5000
            }
        }
        
        test_results = []
        
        for file_path, requirements in js_files.items():
            result = {
                'file': file_path,
                'status': 'unknown',
                'size': 0,
                'content_check': {},
                'issues': []
            }
            
            if os.path.exists(file_path):
                result['status'] = 'exists'
                result['size'] = os.path.getsize(file_path)
                
                # فحص الحد الأدنى للحجم
                if result['size'] < requirements['min_size']:
                    result['issues'].append(f"File too small: {result['size']} < {requirements['min_size']}")
                    self.results['warnings'].append(f"{file_path} may be incomplete")
                
                # فحص المحتوى المطلوب
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for required in requirements['required_content']:
                        if required in content:
                            result['content_check'][required] = True
                        else:
                            result['content_check'][required] = False
                            result['issues'].append(f"Missing required content: {required}")
                            self.results['errors'].append(f"{file_path} missing: {required}")
                    
                    print(f"✅ {file_path} موجود ومحقق")
                
                except Exception as e:
                    result['issues'].append(f"Error reading file: {str(e)}")
                    self.results['errors'].append(f"Cannot read {file_path}: {str(e)}")
            else:
                result['status'] = 'missing'
                result['issues'].append("File does not exist")
                print(f"❌ {file_path} مفقود")
                self.results['errors'].append(f"Required JS file missing: {file_path}")
            
            test_results.append(result)
        
        self.results['tests']['javascript_files'] = test_results
    
    def test_css_files(self):
        """اختبار ملفات CSS"""
        print("🎨 اختبار ملفات CSS...")
        
        css_files = [
            'static/css/style.css'
        ]
        
        test_results = []
        
        for file_path in css_files:
            result = {
                'file': file_path,
                'status': 'unknown',
                'size': 0,
                'offline_styles': False
            }
            
            if os.path.exists(file_path):
                result['status'] = 'exists'
                result['size'] = os.path.getsize(file_path)
                
                # فحص وجود styles للـ offline status bar
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'offline-status-bar' in content:
                        result['offline_styles'] = True
                        print(f"✅ {file_path} يحتوي على offline styles")
                    else:
                        result['offline_styles'] = False
                        self.results['warnings'].append(f"{file_path} missing offline status bar styles")
                        print(f"⚠️ {file_path} لا يحتوي على offline styles")
                
                except Exception as e:
                    self.results['errors'].append(f"Cannot read {file_path}: {str(e)}")
            else:
                result['status'] = 'missing'
                print(f"❌ {file_path} مفقود")
                self.results['errors'].append(f"CSS file missing: {file_path}")
            
            test_results.append(result)
        
        self.results['tests']['css_files'] = test_results
    
    def test_service_worker(self):
        """اختبار Service Worker"""
        print("⚙️ اختبار Service Worker...")
        
        sw_path = 'static/js/service-worker.js'
        result = {
            'file': sw_path,
            'status': 'unknown',
            'cached_pages': [],
            'cached_apis': [],
            'issues': []
        }
        
        if os.path.exists(sw_path):
            result['status'] = 'exists'
            
            try:
                with open(sw_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # استخراج الصفحات المُخزنة
                if 'STATIC_FILES' in content:
                    # البحث عن قائمة الصفحات في Service Worker
                    lines = content.split('\n')
                    in_static_files = False
                    
                    for line in lines:
                        line = line.strip()
                        if 'STATIC_FILES' in line:
                            in_static_files = True
                            continue
                        if in_static_files and line.startswith('"') and '/' in line:
                            page = line.strip('",')
                            if not page.startswith('http'):  # تجاهل CDN links
                                result['cached_pages'].append(page)
                        if in_static_files and '];' in line:
                            break
                
                # استخراج API endpoints المُخزنة
                if 'API_URLS' in content:
                    lines = content.split('\n')
                    in_api_urls = False
                    
                    for line in lines:
                        line = line.strip()
                        if 'API_URLS' in line:
                            in_api_urls = True
                            continue
                        if in_api_urls and line.startswith('"') and '/api/' in line:
                            api = line.strip('",')
                            result['cached_apis'].append(api)
                        if in_api_urls and '];' in line:
                            break
                
                print(f"✅ Service Worker يخزن {len(result['cached_pages'])} صفحة و {len(result['cached_apis'])} API")
                
            except Exception as e:
                result['issues'].append(f"Error parsing Service Worker: {str(e)}")
                self.results['errors'].append(f"Cannot parse Service Worker: {str(e)}")
        else:
            result['status'] = 'missing'
            result['issues'].append("Service Worker file does not exist")
            print(f"❌ Service Worker مفقود")
            self.results['errors'].append("Service Worker file missing")
        
        self.results['tests']['service_worker'] = result
    
    def test_html_templates(self):
        """اختبار قوالب HTML"""
        print("📄 اختبار قوالب HTML...")
        
        # البحث عن جميع ملفات HTML
        template_files = []
        
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        test_results = []
        
        for template_path in template_files:
            result = {
                'file': template_path,
                'status': 'exists',
                'size': os.path.getsize(template_path),
                'base_extends': False,
                'arabic_content': False
            }
            
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # فحص extends base.html
                if 'extends' in content and 'base.html' in content:
                    result['base_extends'] = True
                
                # فحص المحتوى العربي
                arabic_patterns = ['العربية', 'المنتجات', 'العملاء', 'المبيعات']
                if any(pattern in content for pattern in arabic_patterns):
                    result['arabic_content'] = True
                
                print(f"✅ {template_path}")
                
            except Exception as e:
                result['issues'] = [f"Error reading template: {str(e)}"]
                self.results['warnings'].append(f"Cannot read template {template_path}: {str(e)}")
            
            test_results.append(result)
        
        self.results['tests']['html_templates'] = {
            'total_templates': len(test_results),
            'templates': test_results
        }
        
        print(f"📊 تم فحص {len(test_results)} قالب HTML")
    
    def test_api_endpoints(self):
        """اختبار API endpoints من app.py"""
        print("🔗 اختبار API endpoints...")
        
        app_py_path = 'app.py'
        result = {
            'file': app_py_path,
            'api_endpoints': [],
            'offline_endpoints': [],
            'issues': []
        }
        
        if os.path.exists(app_py_path):
            try:
                with open(app_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # البحث عن API routes
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '@app.route(' in line and '/api/' in line:
                        # استخراج المسار من route decorator
                        if "'/api/" in line:
                            start = line.find("'/api/")
                            end = line.find("'", start + 1)
                            if end > start:
                                endpoint = line[start+1:end]
                                result['api_endpoints'].append(endpoint)
                
                # فحص endpoints الأوفلاين المخصصة
                offline_patterns = ['/api/sync', '/api/offline-status']
                for endpoint in result['api_endpoints']:
                    if any(pattern in endpoint for pattern in offline_patterns):
                        result['offline_endpoints'].append(endpoint)
                
                print(f"✅ وُجد {len(result['api_endpoints'])} API endpoint، منها {len(result['offline_endpoints'])} مخصص للأوفلاين")
                
            except Exception as e:
                result['issues'].append(f"Error reading app.py: {str(e)}")
                self.results['errors'].append(f"Cannot read app.py: {str(e)}")
        else:
            result['issues'].append("app.py file does not exist")
            self.results['errors'].append("app.py file missing")
        
        self.results['tests']['api_endpoints'] = result
    
    def test_integration(self):
        """اختبار التكامل بين المكونات"""
        print("🔗 اختبار التكامل...")
        
        result = {
            'base_html_integration': False,
            'js_loading_order': [],
            'css_integration': False,
            'issues': []
        }
        
        # فحص base.html
        base_html_path = 'templates/base.html'
        if os.path.exists(base_html_path):
            try:
                with open(base_html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # فحص تحميل ملفات JS المطلوبة
                js_files = ['db-manager.js', 'sync-manager.js', 'offline-handler.js']
                for js_file in js_files:
                    if js_file in content:
                        result['js_loading_order'].append(js_file)
                
                # فحص تحميل CSS
                if 'style.css' in content:
                    result['css_integration'] = True
                
                # فحص كود التهيئة
                if 'DBManager' in content and 'SyncManager' in content and 'OfflineHandler' in content:
                    result['base_html_integration'] = True
                    print("✅ التكامل في base.html صحيح")
                else:
                    result['issues'].append("Missing initialization code in base.html")
                    self.results['warnings'].append("base.html missing proper offline initialization")
                
            except Exception as e:
                result['issues'].append(f"Error reading base.html: {str(e)}")
                self.results['errors'].append(f"Cannot read base.html: {str(e)}")
        else:
            result['issues'].append("base.html file does not exist")
            self.results['errors'].append("base.html file missing")
        
        self.results['tests']['integration'] = result
    
    def generate_report(self):
        """إنشاء التقرير النهائي"""
        print("📊 إنشاء التقرير النهائي...")
        
        # حساب الإحصائيات
        total_errors = len(self.results['errors'])
        total_warnings = len(self.results['warnings'])
        
        # فحص النجاح العام
        critical_components = [
            'static/js/service-worker.js',
            'static/js/db-manager.js', 
            'static/js/sync-manager.js',
            'static/js/offline-handler.js',
            'templates/base.html'
        ]
        
        missing_critical = []
        for component in critical_components:
            if not os.path.exists(component):
                missing_critical.append(component)
        
        # تحديد حالة النجاح
        if total_errors == 0 and len(missing_critical) == 0:
            status = "SUCCESS"
            status_emoji = "✅"
        elif len(missing_critical) > 0:
            status = "CRITICAL_FAILURE"
            status_emoji = "❌"
        elif total_errors > 0:
            status = "PARTIAL_SUCCESS"
            status_emoji = "⚠️"
        else:
            status = "SUCCESS_WITH_WARNINGS"
            status_emoji = "✅"
        
        self.results['summary'] = {
            'overall_status': status,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'missing_critical_components': missing_critical,
            'test_categories': list(self.results['tests'].keys())
        }
        
        # طباعة التقرير
        print("\n" + "="*80)
        print(f"{status_emoji} تقرير الاختبار الشامل للصفحات الأوفلاين")
        print("="*80)
        print(f"الحالة العامة: {status}")
        print(f"عدد الأخطاء: {total_errors}")
        print(f"عدد التحذيرات: {total_warnings}")
        
        if missing_critical:
            print(f"\n❌ مكونات حرجة مفقودة:")
            for component in missing_critical:
                print(f"  - {component}")
        
        if self.results['errors']:
            print(f"\n❌ الأخطاء:")
            for error in self.results['errors'][:10]:  # عرض أول 10 أخطاء
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... و {len(self.results['errors']) - 10} أخطاء أخرى")
        
        if self.results['warnings']:
            print(f"\n⚠️ التحذيرات:")
            for warning in self.results['warnings'][:5]:  # عرض أول 5 تحذيرات
                print(f"  - {warning}")
            if len(self.results['warnings']) > 5:
                print(f"  ... و {len(self.results['warnings']) - 5} تحذيرات أخرى")
        
        # توصيات
        print(f"\n💡 التوصيات:")
        if status == "SUCCESS":
            print("  ✅ جميع المكونات جاهزة للعمل الأوفلاين!")
            print("  🚀 يمكنك الآن اختبار التطبيق في الوضع الأوفلاين")
        elif status == "CRITICAL_FAILURE":
            print("  ❌ يجب إنشاء المكونات المفقودة أولاً")
            print("  🔧 تأكد من وجود جميع ملفات JavaScript والقوالب")
        else:
            print("  ⚠️ بعض المكونات تحتاج إلى تحسين")
            print("  🔍 راجع الأخطاء والتحذيرات أعلاه")
        
        print("="*80)
        
        # حفظ التقرير في ملف
        report_file = f"offline_test_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 تم حفظ التقرير الكامل في: {report_file}")

def main():
    """الدالة الرئيسية"""
    tester = OfflineComprehensiveTest()
    results = tester.run_all_tests()
    
    # إرجاع كود الخروج المناسب
    if results['summary']['overall_status'] == 'SUCCESS':
        sys.exit(0)
    elif results['summary']['overall_status'] == 'CRITICAL_FAILURE':
        sys.exit(2)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 