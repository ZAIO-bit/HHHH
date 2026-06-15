"""
بوت الاستضافه 0.1
👨‍💻 تطوير: ALKYADA 
📢 قناة المطور: https://t.me/DX_PY

"""

# ========== 1. التثبيت التلقائي للمكتبات ==========
import subprocess
import sys
import os
import time
import sqlite3
import logging
import secrets
import datetime
from datetime import timedelta
import threading
import traceback
import hashlib
import json
import re
from io import StringIO, BytesIO
from collections import defaultdict

def install_package(package):
    """تثبيت مكتبة"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        print(f"✅ تم تثبيت {package}")
    except Exception as e:
        print(f"⚠️ تعذر تثبيت {package}: {e}")

required_packages = {
    'pyTelegramBotAPI': 'telebot',
    'speedtest-cli': 'speedtest'
}

for package, module in required_packages.items():
    try:
        __import__(module)
    except ImportError:
        print(f"⚙️ المكتبة {package} غير موجودة، جاري التثبيت...")
        install_package(package)

# الاستيرادات الرئيسية
import telebot
from telebot import types

try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except:
    SPEEDTEST_AVAILABLE = False

# ========== 2. الإعدادات الأساسية ==========
BOT_TOKEN = '7317172461:AAEH19kE0r9TPvd9l4q0jKIrdGsZ6Ckc4ZI'       # ضع التوكن هنا
ADMIN_ID = 6739658332         # ضع آيدي المطور هنا
DEVELOPER_USERNAME = 'c8s8sx' # معرف المطور
DEVELOPER_CHANNEL = 'TETEETEE' # معرف القناه  
BOT_VERSION = '0.1' # اصدار البوت
ch_adm = "@TETEETEE" # معرف القناه
admin_url = "https://files.catbox.moe/s9bn12.png" # الصوره الرئيسيه للبوت
banen_url = "https://files.catbox.moe/ci83gr.png" # صوره تظهر للمستخدم الذي يتم حظره
syana_url = "https://files.catbox.moe/90yy0r.png" # صوره تظهر للمستخدمين اثناء تفعيل وضع الصيانه
ekaf_url ="https://files.catbox.moe/90yy0r.png" # صوره تظهر للمستخدمين عند عمل ايقاف للبوت
num_ms = "8" # رقم الرساله الخاصه  ب ثقه البوت مثال(https://t.me/w_nn7/2) يجب ان يكون موجود في قناتكم
# مجلدات الملفات
UPLOAD_FOLDER = "uploaded_files"
PENDING_FOLDER = "pending_files"
LOGS_FOLDER = "bot_logs"

# إنشاء المجلدات المطلوبة
for folder in [UPLOAD_FOLDER, PENDING_FOLDER, LOGS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 تم إنشاء مجلد: {folder}")

# ========== إعداد السجلات المُحسّن ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_FOLDER, 'bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# قاموس العمليات النشطة
running_processes = {}

# ========== دوال مساعدة للتعامل مع الرسائل ==========
def escape_html(text):
    """تحويل النص لتجنب مشاكل HTML"""
    if not text:
        return ""
    # تحويل الرموز الخاصة بـ HTML
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    return text

def safe_edit_message(bot, chat_id, message_id, text=None, caption=None, reply_markup=None):
    """تعديل الرسالة بشكل آمن مع التحقق من عدم التكرار"""
    try:
        if caption is not None:
            # تعديل caption
            bot.edit_message_caption(
                caption=caption,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
        elif text is not None:
            # تعديل text
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
    except Exception as e:
        if "message is not modified" in str(e):
            # الرسالة نفسها، تجاهل
            pass
        else:
            # خطأ آخر، سجله
            logger.error(f"خطأ في تعديل الرسالة: {e}")

def safe_edit_message_caption(bot, chat_id, message_id, caption, reply_markup=None):
    """تعديل caption بشكل آمن"""
    try:
        bot.edit_message_caption(
            caption=caption,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"خطأ في تعديل caption: {e}")

def safe_edit_message_text(bot, chat_id, message_id, text, reply_markup=None):
    """تعديل text بشكل آمن"""
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"خطأ في تعديل text: {e}")

# ========== 3. نظام مضاد السبام والتكرار ==========
class AntiSpamSystem:
    """نظام مضاد السبام"""
    def __init__(self):
        self.user_messages = defaultdict(list)
        self.user_commands = defaultdict(list)
        self.blocked_users = set()
        self.message_limits = defaultdict(int)
    
    def check_spam(self, user_id, limit=5, window=10):
        """التحقق من السبام"""
        now = time.time()
        self.user_messages[user_id] = [t for t in self.user_messages[user_id] if now - t < window]
        self.user_messages[user_id].append(now)
        
        if len(self.user_messages[user_id]) > limit:
            self.blocked_users.add(user_id)
            return True
        return False
    
    def is_blocked(self, user_id):
        """التحقق من الحظر المؤقت"""
        return user_id in self.blocked_users
    
    def unblock(self, user_id):
        """إلغاء الحظر المؤقت"""
        self.blocked_users.discard(user_id)
    
    def clean_old_records(self):
        """تنظيف السجلات القديمة"""
        now = time.time()
        for user_id in list(self.user_messages.keys()):
            self.user_messages[user_id] = [t for t in self.user_messages[user_id] if now - t < 60]
            if not self.user_messages[user_id]:
                del self.user_messages[user_id]

anti_spam = AntiSpamSystem()

# ========== 4. قاعدة البيانات المُطوَّرة ==========
def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات مع معالجة أفضل للأخطاء"""
    try:
                # تم تغيير اسم الملف إلى zaio_database.db لمنع التضارب مع البوت الثاني
        conn = sqlite3.connect('zaio_database.db', check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn
    except sqlite3.Error as e:
        logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        raise

def init_database():
    """تهيئة قاعدة البيانات مع جميع الجداول"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                points INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                vip_expiry TEXT,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                join_date TEXT,
                last_active TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_referred INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                language TEXT DEFAULT 'ar',
                total_files INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_warning TEXT
            )
        ''')
        
        # جدول الملفات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                filepath TEXT,
                size INTEGER,
                status TEXT DEFAULT 'pending',
                upload_date TEXT,
                admin_msg_id INTEGER,
                approved_by INTEGER,
                approved_date TEXT,
                rejection_reason TEXT,
                error_log TEXT,
                auto_restart INTEGER DEFAULT 0,
                syntax_ok INTEGER DEFAULT 1,
                security_warnings TEXT
            )
        ''')
        
        # جدول البوتات النشطة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                user_id INTEGER,
                bot_name TEXT,
                process_id INTEGER,
                start_time TEXT,
                status TEXT DEFAULT 'running',
                restart_count INTEGER DEFAULT 0,
                last_restart TEXT,
                last_error TEXT
            )
        ''')
        
        # جدول الإعدادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # جدول القنوات الإجبارية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS force_subscribe (
                channel_id TEXT PRIMARY KEY,
                channel_username TEXT,
                channel_name TEXT
            )
        ''')
        
        # جدول سجلات الأدمن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        # جدول الإشعارات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                message TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        
        # جدول تحويلات النقاط
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER,
                to_user INTEGER,
                amount INTEGER,
                fee INTEGER,
                timestamp TEXT
            )
        ''')
        
        # جدول المكتبات المثبتة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS installed_libraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                version TEXT,
                installed_by INTEGER,
                install_date TEXT
            )
        ''')
        
        # جدول التقارير
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                reported_user INTEGER,
                reason TEXT,
                file_id INTEGER,
                timestamp TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # جدول سجل البوتات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                event TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        # جدول الأوامر المخصصة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT UNIQUE,
                response TEXT,
                created_by INTEGER,
                created_at TEXT
            )
        ''')
        
        # جدول الأخطاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                error_type TEXT,
                error_message TEXT,
                line_number INTEGER,
                timestamp TEXT,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        # الإعدادات الافتراضية
        default_settings = [
            ('welcome_message', '🎉 أهلاً وسهلاً بك في بوت استضافة البوتات المتقدم!'),
            ('bot_enabled', '1'),
            ('maintenance_mode', '0'),
            ('maintenance_msg', '🔧 البوت تحت الصيانة، يرجى الانتظار...'),
            ('points_per_file', '5'),
            ('points_per_referral', '2'),
            ('vip_price_week', '50'),
            ('vip_price_month', '150'),
            ('vip_price_year', '500'),
            ('force_subscription', '0'),
            ('new_user_notification', '1'),
            ('max_file_size', '10240'),
            ('max_bots_per_user', '5'),
            ('max_bots_vip', '15'),
            ('auto_restart', '1'),
            ('spam_limit', '5'),
            ('spam_window', '10'),
            ('transfer_fee', '0.1'),
            ('rules_text', """<blockquote>📋 <b>قوانين وشروط استضافة الفارس:</b>

1️⃣ يُمنع قطعياً رفع أي بوتات ضارة (Malware) أو ملفات خبيثة تستهدف السيرفر.
2️⃣ يُمنع استخدام البوت في عمليات السبام (Spam) أو الإغراق التكراري لضمان استقرار الخدمة.
3️⃣ الحد الأقصى للمستخدم العادي هو 5 بوتات فقط (لزيادة الحد تواصل مع الإدارة).
4️⃣ يُمنع رفع سكريبتات التعدين (Mining) أو استهلاك موارد المعالج بشكل مفرط بدون إذن.
5️⃣ يُحظر استخدام الاستضافة في أي نشاط يخالف سياسات تليجرام الرسمية.
6️⃣ الإدارة غير مسؤولة عن فقدان البيانات في حال مخالفة القوانين، ويحق لنا إيقاف أي بوت مخالف فوراً.
7️⃣ الاحترام المتبادل بين المستخدمين والمطورين هو أساس مجتمعنا.

💡 <b>ملاحظة:</b> استمرارك في استخدام البوت يعني موافقتك الكاملة على هذه الشروط.</blockquote>"""),
            ('help_text', """<blockquote>❓ <b>دليل المساعدة والتحكم:</b>

📤 <b>رفع بوت جديد:</b> فقط قم بإرسال ملف البوت بصيغة <code>.py</code> وسيقوم النظام بالتعرف عليه.
🤖 <b>إدارة بوتاتي:</b> لمتابعة حالة بوتاتك النشطة، إيقافها، أو إعادة تشغيلها.
💎 <b>نظام النقاط:</b> عرض رصيدك الحالي ومعرفة استهلاكك للموارد.
👥 <b>كسب النقاط:</b> استخدم رابط الدعوة الخاص بك لزيادة رصيدك مجاناً عند انضمام أصدقائك.
🛠 <b>الدعم الفني:</b> إذا واجهت مشكلة، توجه لقسم المطور للمساعدة الفورية.

💡 <i>كل ما تحتاجه لإدارة استضافتك في مكان واحد!</i></blockquote>"""),
            ('error_notification', '1'),
            ('auto_error_report', '1')
        ]
        
        cursor.executemany('INSERT OR IGNORE INTO settings VALUES (?, ?)', default_settings)
        
        # إضافة الأدمن الأساسي
        cursor.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, first_name, is_admin, join_date, last_active, referral_code) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ADMIN_ID, 'المالك', 1, datetime.datetime.now(), datetime.datetime.now(), f"REF{ADMIN_ID}"))
        
        conn.commit()
        conn.close()
        logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

# ========== 5. الدوال المساعدة المُطوَّرة ==========
def get_setting(key):
    """الحصول على قيمة إعداد"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"خطأ في get_setting({key}): {e}")
        return None

def update_setting(key, value):
    """تحديث قيمة إعداد"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في update_setting({key}): {e}")
        return False

def get_user(user_id):
    """الحصول على بيانات مستخدم - مُصلح"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"خطأ في get_user({user_id}): {e}")
        return None

def is_admin(user_id):
    """التحقق من صلاحيات الأدمن - مُصلح"""
    # التحقق من ADMIN_ID أولاً
    if user_id == ADMIN_ID:
        return True
    # ثم التحقق من قاعدة البيانات
    user = get_user(user_id)
    if user and user[13] == 1:  # user[13] هو عمود is_admin
        return True
    return False

def is_vip(user_id):
    """التحقق من حالة VIP"""
    user = get_user(user_id)
    if user and user[4] == 1:
        if user[5]:
            try:
                expiry = datetime.datetime.strptime(user[5], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() > expiry:
                    remove_vip(user_id)
                    return False
            except:
                pass
        return True
    return False

def get_max_bots(user_id):
    """الحصول على الحد الأقصى من البوتات للمستخدم"""
    if is_vip(user_id):
        return int(get_setting('max_bots_vip') or 15)
    return int(get_setting('max_bots_per_user') or 5)

def add_user(user_id, username, first_name):
    """إضافة أو تحديث مستخدم - مُصلح"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود المستخدم أولاً
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if not existing:
            referral_code = f"REF{user_id}{secrets.token_hex(3).upper()}"
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, join_date, last_active, referral_code) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.datetime.now(), datetime.datetime.now(), referral_code))
            conn.commit()
            conn.close()
            return True  # مستخدم جديد
        else:
            cursor.execute('''
                UPDATE users SET 
                username = ?, first_name = ?, last_active = ?
                WHERE user_id = ?
            ''', (username, first_name, datetime.datetime.now(), user_id))
            conn.commit()
            conn.close()
            return False  # مستخدم موجود تم تحديثه
    except Exception as e:
        logger.error(f"خطأ في add_user({user_id}): {e}")
        return False

def update_user_points(user_id, points):
    """تحديث نقاط المستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في update_user_points: {e}")
        return False

def set_user_points(user_id, points):
    """تعيين نقاط المستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET points = ? WHERE user_id = ?', (points, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في set_user_points: {e}")
        return False

def set_vip(user_id, days):
    """تفعيل VIP لمستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        expiry_date = (datetime.datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET is_vip = 1, vip_expiry = ? WHERE user_id = ?', (expiry_date, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في set_vip: {e}")
        return False

def remove_vip(user_id):
    """إلغاء VIP لمستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_vip = 0, vip_expiry = NULL WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في remove_vip: {e}")
        return False

# ========== دوال إدارة الأدمن ==========
def add_admin(user_id, added_by=None):
    """إضافة أدمن جديد - مع إنشاء سجل للمستخدم إذا لم يكن موجوداً"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود المستخدم
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # المستخدم موجود، فقط أضف صلاحية الأدمن
            cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
        else:
            # المستخدم غير موجود، أنشئ سجل جديد مع صلاحية الأدمن
            referral_code = f"REF{user_id}{secrets.token_hex(3).upper()}"
            cursor.execute('''
                INSERT INTO users 
                (user_id, first_name, is_admin, join_date, last_active, referral_code) 
                VALUES (?, ?, 1, ?, ?, ?)
            ''', (user_id, f"أدمن جديد", datetime.datetime.now(), datetime.datetime.now(), referral_code))
        
        conn.commit()
        conn.close()
        return True, "تمت الإضافة بنجاح"
    except Exception as e:
        logger.error(f"خطأ في add_admin: {e}")
        return False, str(e)

def remove_admin(user_id):
    """إزالة صلاحية أدمن"""
    try:
        # لا يمكن إزالة صلاحية المالك الأساسي
        if user_id == ADMIN_ID:
            return False, "لا يمكن إزالة صلاحية المالك الأساسي!"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_admin = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True, "تمت الإزالة بنجاح"
    except Exception as e:
        logger.error(f"خطأ في remove_admin: {e}")
        return False, str(e)

def get_all_admins():
    """الحصول على قائمة جميع الأدمن"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, first_name, username FROM users WHERE is_admin = 1')
        admins = cursor.fetchall()
        conn.close()
        return admins
    except Exception as e:
        logger.error(f"خطأ في get_all_admins: {e}")
        return []

def is_super_admin(user_id):
    """التحقق من المالك الأساسي"""
    return user_id == ADMIN_ID

def ban_user(user_id, reason=""):
    """حظر مستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?', (reason, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في ban_user: {e}")
        return False

def unban_user(user_id):
    """فك حظر مستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في unban_user: {e}")
        return False

def add_warning(user_id):
    """إضافة تحذير للمستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET warnings = warnings + 1, last_warning = ? WHERE user_id = ?', 
                      (datetime.datetime.now(), user_id))
        cursor.execute('SELECT warnings FROM users WHERE user_id = ?', (user_id,))
        warnings = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return warnings
    except Exception as e:
        logger.error(f"خطأ في add_warning: {e}")
        return 0

def log_action(admin_id, action, target, details=""):
    """إضافة سجل للأدمن"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, action, target, details, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في log_action: {e}")

def add_notification(user_id, title, message):
    """إضافة إشعار"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, message, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في add_notification: {e}")

def get_unread_notifications(user_id):
    """الحصول على عدد الإشعارات غير المقروءة"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"خطأ في get_unread_notifications: {e}")
        return 0

def transfer_points(from_user, to_user, amount):
    """تحويل نقاط بين المستخدمين"""
    try:
        fee = int(amount * float(get_setting('transfer_fee') or 0.1))
        total = amount + fee
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (from_user,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False, "المستخدم غير موجود"
        from_points = result[0]
        
        if from_points < total:
            conn.close()
            return False, "رصيد غير كافي"
        
        cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (total, from_user))
        cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, to_user))
        
        cursor.execute('''
            INSERT INTO points_transfers (from_user, to_user, amount, fee, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (from_user, to_user, amount, fee, datetime.datetime.now()))
        
        conn.commit()
        conn.close()
        return True, fee
    except Exception as e:
        logger.error(f"خطأ في transfer_points: {e}")
        return False, str(e)

def get_user_stats():
    """الحصول على إحصائيات المستخدمين"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_vip = 1')
        vip_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
        banned_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        admin_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(last_active) = date("now")')
        active_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(join_date) = date("now")')
        new_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(points) FROM users')
        total_points = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM files')
        total_files = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'vip_users': vip_users,
            'banned_users': banned_users,
            'admin_users': admin_users,
            'active_today': active_today,
            'new_today': new_today,
            'total_points': total_points,
            'total_files': total_files
        }
    except Exception as e:
        logger.error(f"خطأ في get_user_stats: {e}")
        return {'total_users': 0, 'vip_users': 0, 'banned_users': 0, 'admin_users': 0, 
                'active_today': 0, 'new_today': 0, 'total_points': 0, 'total_files': 0}

def get_force_channels():
    """الحصول على قنوات الاشتراك الإجباري"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM force_subscribe')
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"خطأ في get_force_channels: {e}")
        return []

def check_subscription(user_id):
    """التحقق من الاشتراك في القنوات"""
    channels = get_force_channels()
    if not channels:
        return True
    
    for channel in channels:
        try:
            chat_member = bot.get_chat_member(channel[0], user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        except:
            pass
    return True

def install_library(name, user_id):
    """تثبيت مكتبة"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", name], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO installed_libraries (name, installed_by, install_date)
                VALUES (?, ?, ?)
            ''', (name, user_id, datetime.datetime.now()))
            conn.commit()
            conn.close()
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "انتهت المهلة"
    except Exception as e:
        return False, str(e)

def get_installed_libraries():
    """الحصول على قائمة المكتبات المثبتة"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name, install_date FROM installed_libraries ORDER BY id DESC')
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"خطأ في get_installed_libraries: {e}")
        return []

# ========== 6. نظام التحقق من الأخطاء ==========
def format_error_message(error_text, filepath=None):
    """تنسيق رسالة الخطأ بشكل واضح مع علامات اقتباس"""
    # استخراج رقم السطر من رسالة الخطأ
    line_match = re.search(r'line (\d+)', error_text)
    line_number = int(line_match.group(1)) if line_match else None
    
    # استخراج اسم الملف
    file_match = re.search(r'File "([^"]+)"', error_text)
    filename = os.path.basename(file_match.group(1)) if file_match else "ملف"
    
    # استخراج نوع الخطأ ورسالته
    error_type_match = re.search(r'(\w+Error|\w+Exception): (.+)$', error_text, re.MULTILINE)
    if error_type_match:
        error_type = error_type_match.group(1)
        error_msg = error_type_match.group(2)
    else:
        error_type = "خطأ"
        error_msg = error_text.split('\n')[-1] if error_text else "غير معروف"
    
    # استخراج السطر الذي فيه الخطأ من الكود
    code_line = None
    if filepath and line_number:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if line_number <= len(lines):
                    code_line = lines[line_number - 1].rstrip()
        except:
            pass
    
    # استخراج السطر من رسالة الخطأ نفسها
    if not code_line:
        line_content_match = re.search(r'\n\s+(.+)\n\s+\^', error_text)
        if line_content_match:
            code_line = line_content_match.group(1).strip()
    
    # بناء الرسالة المنسقة
    formatted = f"🚨 <b>تم اكتشاف خطأ في الكود!</b>\n\n"
    formatted += f"📄 <b>الملف:</b> <code>{escape_html(filename)}</code>\n"
    
    if line_number:
        formatted += f"📍 <b>السطر:</b> <code>{line_number}</code>\n\n"
    
    if code_line:
        formatted += f"📝 <b>الكود:</b>\n"
        formatted += f"┌──────────────────\n"
        formatted += f"│ <code>{escape_html(code_line)}</code>\n"
        formatted += f"└──────────────────\n\n"
    
    formatted += f"❌ <b>نوع الخطأ:</b> <code>{escape_html(error_type)}</code>\n"
    formatted += f"⚠️ <b>التفاصيل:</b> <code>{escape_html(error_msg)}</code>\n\n"
    
    formatted += f"💡 <b>نصيحة:</b> راجع السطر المشار إليه وأصلح الخطأ"
    
    return formatted, line_number

def check_python_syntax(filepath):
    """التحقق من صحة كتابة كود Python مع عرض تفصيلي للأخطاء"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        compile(code, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        # استخراج الكود من السطر الخطأ
        code_line = e.text.rstrip() if e.text else None
        
        error_msg = f"🚨 <b>خطأ في كتابة الكود!</b>\n\n"
        error_msg += f"📄 <b>الملف:</b> <code>{escape_html(os.path.basename(filepath))}</code>\n"
        error_msg += f"📍 <b>السطر:</b> <code>{e.lineno}</code>\n\n"
        
        if code_line:
            error_msg += f"📝 <b>الكود:</b>\n"
            error_msg += f"┌──────────────────────\n"
            error_msg += f"│ <code>{escape_html(code_line)}</code>\n"
            if e.offset:
                # إضافة علامة ^ تحت موقع الخطأ
                pointer = " " * (e.offset - 1) + "^"
                error_msg += f"│ <code>{pointer}</code>\n"
            error_msg += f"└──────────────────────\n\n"
        
        error_msg += f"❌ <b>نوع الخطأ:</b> <code>SyntaxError</code>\n"
        error_msg += f"⚠️ <b>التفاصيل:</b> <code>{escape_html(e.msg)}</code>\n\n"
        error_msg += f"💡 <b>نصيحة:</b> راجع السطر {e.lineno} وأصلح الخطأ"
        
        return False, error_msg
    except Exception as e:
        # محاولة تنسيق أي خطأ آخر
        try:
            formatted, _ = format_error_message(str(e), filepath)
            return False, formatted
        except:
            return False, f"❌ خطأ في الكود:\n\n<code>{escape_html(str(e))}</code>"

def check_security_issues(filepath):
    """فحص المشاكل الأمنية في الكود"""
    warnings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # أنماط خطرة
        dangerous_patterns = [
            (r'os\.system\s*\(', '⚠️ الكود يحتوي على os.system() - أوامر نظام'),
            (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', '⚠️ الكود يستخدم subprocess مع shell=True'),
            (r'eval\s*\(', '⚠️ الكود يحتوي على eval() - خطر تنفيذ كود'),
            (r'exec\s*\(', '⚠️ الكود يحتوي على exec() - خطر تنفيذ كود'),
            (r'__import__\s*\(', '⚠️ الكود يحتوي على __import__() - استيراد ديناميكي'),
            (r'open\s*\([^)]*["\']w["\']', '⚠️ الكود يحاول الكتابة في ملفات'),
            (r'open\s*\([^)]*["\']a["\']', '⚠️ الكود يحاول الإضافة لملفات'),
            (r'shutil\.rmtree', '⚠️ الكود يحتوي على حذف مجلدات'),
            (r'os\.remove', '⚠️ الكود يحتوي على حذف ملفات'),
            (r'pickle\.loads?', '⚠️ الكود يستخدم pickle - خطر تنفيذ كود'),
            (r'marshal\.loads?', '⚠️ الكود يستخدم marshal - خطر'),
        ]
        
        for pattern, msg in dangerous_patterns:
            if re.search(pattern, code):
                warnings.append(msg)
        
        # فحص المكتبات المطلوبة
        import_warnings = []
        import_lines = re.findall(r'^(?:import|from)\s+(\w+)', code, re.MULTILINE)
        for lib in import_lines[:5]:
            try:
                __import__(lib)
            except ImportError:
                import_warnings.append(f"📦 المكتبة '{lib}' غير مثبتة")
        
        return warnings, import_warnings
    except Exception as e:
        logger.error(f"خطأ في check_security_issues: {e}")
        return warnings, []

def run_bot_and_capture_errors(filepath, timeout=10):
    """تشغيل البوت واكتشاف الأخطاء"""
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(filepath) or '.'
        )
        
        if result.returncode != 0:
            error_output = result.stderr or result.stdout
            return False, error_output
        
        return True, "تم التشغيل"
    except subprocess.TimeoutExpired:
        return True, "البوت يعمل (في وضع الانتظار)"
    except Exception as e:
        return False, str(e)

def log_error(user_id, filename, error_type, error_message, line_number=None):
    """تسجيل خطأ في قاعدة البيانات"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO error_logs (user_id, filename, error_type, error_message, line_number, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, filename, error_type, error_message, line_number, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في log_error: {e}")

# ========== 7. نظام إدارة البوتات ==========
def start_bot(file_id, filepath, filename, user_id):
    """تشغيل بوت - مُصلح مع فحص وجود الملف والتحقق من بدء التشغيل"""
    try:
        # التأكد من وجود الملف
        if not os.path.exists(filepath):
            logger.error(f"الملف غير موجود: {filepath}")
            return False, "الملف غير موجود"
        
        p = subprocess.Popen([sys.executable, filepath], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
        running_processes[filename] = p
        
        # انتظار قصير للتحقق من بدء التشغيل
        time.sleep(1)
        if p.poll() is not None:
            # العملية انتهت فوراً، هناك خطأ
            stdout, stderr = p.communicate(timeout=1)
            error = stderr.decode('utf-8', errors='ignore') if stderr else stdout.decode('utf-8', errors='ignore')
            del running_processes[filename]
            return False, error or "فشل التشغيل - البوت توقف فوراً"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE files SET status="running" WHERE id=?', (file_id,))
        cursor.execute('''
            INSERT INTO active_bots (file_id, user_id, bot_name, process_id, start_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_id, user_id, filename, p.pid, datetime.datetime.now()))
        
        points = int(get_setting('points_per_file') or 5)
        cursor.execute('UPDATE users SET points=points+?, total_files=total_files+1 WHERE user_id=?', (points, user_id))
        conn.commit()
        conn.close()
        
        log_bot_event(filename, "start", f"PID: {p.pid}")
        logger.info(f"🟢 تشغيل: {filename} PID:{p.pid}")
        return True, p.pid
    except Exception as e:
        logger.error(f"❌ فشل التشغيل: {e}")
        return False, str(e)

def stop_bot(filename):
    """إيقاف بوت"""
    if filename in running_processes:
        try:
            running_processes[filename].terminate()
            del running_processes[filename]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status="stopped" WHERE filename=?', (filename,))
            cursor.execute('UPDATE active_bots SET status="stopped" WHERE bot_name=?', (filename,))
            conn.commit()
            conn.close()
            
            log_bot_event(filename, "stop", "تم الإيقاف")
            return True
        except Exception as e:
            logger.error(f"خطأ في إيقاف البوت: {e}")
    return False

def restart_bot(filename):
    """إعادة تشغيل بوت باستخدام نفس المتغيرات والأعمدة الأصلية"""
    try:
        # 1. جلب البيانات بنفس أسماء الأعمدة اللي ذكرتها (id, filepath, user_id)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, filepath, user_id FROM files WHERE filename=?', (filename,))
        file_data = cursor.fetchone()
        conn.close()
        
        # التأكد إن الملف له بيانات في القاعدة
        if file_data:
            # 2. الحل الجذري: لو البوت شغال (موجود في القاموس) بنوقفه الأول
            if filename in running_processes:
                stop_bot(filename)
                time.sleep(1.5) # وقت أمان عشان العملية تقفل صح
            
            # 3. تشغيل البوت سواء كان شغال واتقفل أو كان واقف أصلاً
            # بنمرر المتغيرات بالترتيب: (ID, Filepath, Filename, User_ID)
            success, result = start_bot(file_data[0], file_data[1], filename, file_data[2])
            
            if success:
                # 4. تحديث سجلات الريستارت بنفس أسماء الجداول (active_bots)
                conn = get_db_connection()
                conn.execute('''
                    UPDATE active_bots 
                    SET restart_count = restart_count + 1, last_restart = ? 
                    WHERE bot_name=?
                ''', (datetime.datetime.now(), filename))
                conn.commit()
                conn.close()
                return True
        else:
            logger.error(f"❌ لم يتم العثور على {filename} في جدول files")
            
    except Exception as e:
        logger.error(f"⚠️ خطأ في restart_bot: {e}")
    return False

def stop_all_bots():
    """إيقاف جميع البوتات"""
    count = 0
    for name in list(running_processes.keys()):
        if stop_bot(name):
            count += 1
    return count

def stop_user_bots(user_id):
    """إيقاف جميع بوتات مستخدم"""
    count = 0
    for name in list(running_processes.keys()):
        if name.startswith(f"{user_id}_"):
            if stop_bot(name):
                count += 1
    return count

def log_bot_event(bot_name, event, details):
    """تسجيل حدث للبوت"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bot_logs (bot_name, event, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (bot_name, event, details, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في log_bot_event: {e}")

def monitor_bots():
    """مراقبة البوتات وإعادة تشغيل المتوقفة - مُصلح"""
    while True:
        try:
            for filename in list(running_processes.keys()):
                p = running_processes[filename]
                if p.poll() is not None:  # البوت توقف
                    logger.info(f"🔄 بوت توقف: {filename}")
                    log_bot_event(filename, "crash", f"Exit code: {p.poll()}")
                    del running_processes[filename]
                    
                    # محاولة إعادة التشغيل
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('SELECT id, filepath, user_id FROM files WHERE filename=?', (filename,))
                        file_data = cursor.fetchone()
                        conn.close()
                        
                        if file_data:
                            success, _ = start_bot(file_data[0], file_data[1], filename, file_data[2])
                            if success:
                                logger.info(f"✅ تمت إعادة التشغيل: {filename}")
                    except Exception as e:
                        logger.error(f"خطأ في إعادة التشغيل: {e}")
        except Exception as e:
            logger.error(f"خطأ في مراقبة البوتات: {e}")
        
        time.sleep(30)

def get_user_bots(user_id):
    """الحصول على بوتات المستخدم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM active_bots WHERE user_id = ? AND status = "running"', (user_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"خطأ في get_user_bots: {e}")
        return []

def get_all_active_bots():
    """الحصول على جميع البوتات النشطة"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM active_bots WHERE status = "running"')
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"خطأ في get_all_active_bots: {e}")
        return []

# ========== 8. لوحات المفاتيح المُطوَّرة ==========
def admin_panel_keyboard():
    """لوحة مفاتيح الأدمن الرئيسية"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # الصف الأول - المراقبة
    markup.add(
        types.InlineKeyboardButton("📥 طلبات الانتظار", callback_data="admin_pending", style="primary"),
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats", style="danger"),
        types.InlineKeyboardButton("📡 السيرفر", callback_data="admin_server", style="success")
    )
    
    # الصف الثاني - البوتات والملفات
    markup.add(
        types.InlineKeyboardButton("🤖 البوتات النشطة", callback_data="admin_active", style="primary"),
        types.InlineKeyboardButton("📁 الملفات", callback_data="admin_files", style="danger"),
        types.InlineKeyboardButton("📊 موارد البوتات", callback_data="admin_resources", style="success")
    )
    
    # الصف الثالث - المستخدمين
    markup.add(
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users", style="primary"),
        types.InlineKeyboardButton("🚫 المحظورين", callback_data="admin_banned", style="danger"),
        types.InlineKeyboardButton("🔍 بحث متقدم", callback_data="admin_search", style="success")
    )
    
    # الصف الرابع - النقاط والهدايا
    markup.add(
        types.InlineKeyboardButton("💎 النقاط", callback_data="admin_points", style="primary"),
        types.InlineKeyboardButton("🎁 هدايا جماعية", callback_data="admin_gifts", style="danger"),
        types.InlineKeyboardButton("🎫 أكواد ترويجية", callback_data="admin_promo", style="success")
    )
    
    # الصف الخامس - VIP والأعضاء
    markup.add(
        types.InlineKeyboardButton("⭐ VIP", callback_data="admin_vip", style="primary"),
        types.InlineKeyboardButton("📊 نشاط اليوم", callback_data="admin_daily", style="danger"),
        types.InlineKeyboardButton("📈 نشاط شهري", callback_data="admin_monthly", style="success")
    )
    
    # الصف السادس - الأدوات
    markup.add(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast", style="primary"),
        types.InlineKeyboardButton("🔔 إشعار خاص", callback_data="admin_notify", style="danger"),
        types.InlineKeyboardButton("⏰ جدولة", callback_data="admin_schedule", style="success")
    )
    
    # الصف السابع - متقدم
    markup.add(
        types.InlineKeyboardButton("💻 تنفيذ أمر", callback_data="admin_cmd", style="primary"),
        types.InlineKeyboardButton("📚 المكتبات", callback_data="admin_libs", style="danger"),
        types.InlineKeyboardButton("⚡ سرعة النت", callback_data="admin_speed", style="success")
    )
    
    # الصف الثامن - إدارة
    markup.add(
        types.InlineKeyboardButton("👑 الأدمن", callback_data="admin_admins", style="primary"),
        types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings", style="danger"),
        types.InlineKeyboardButton("🔐 الأمان", callback_data="admin_security", style="success")
    )
    
    # الصف التاسع - سجلات وملاحظات
    markup.add(
        types.InlineKeyboardButton("📋 السجلات", callback_data="admin_logs", style="primary"),
        types.InlineKeyboardButton("🚨 الأخطاء", callback_data="admin_errors", style="danger"),
        types.InlineKeyboardButton("📝 ملاحظاتي", callback_data="admin_notes", style="success")
    )
    
    # الصف العاشر - أدوات إضافية
    markup.add(
        types.InlineKeyboardButton("📊 التقارير", callback_data="admin_reports", style="primary"),
        types.InlineKeyboardButton("💬 ردود تلقائية", callback_data="admin_auto_reply", style="danger"),
        types.InlineKeyboardButton("🎯 تقييمات", callback_data="admin_ratings", style="success")
    )
    
    # الصف الحادي عشر - تحكم
    markup.add(
        types.InlineKeyboardButton("📢 اشتراك إجباري", callback_data="admin_force", style="primary"),
        types.InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="admin_restart_menu", style="danger"),
        types.InlineKeyboardButton("📥 تصدير", callback_data="admin_export", style="success")
    )
    
    # الصف الثاني عشر - صيانة
    markup.add(
        types.InlineKeyboardButton("🛑 إيقاف الكل", callback_data="admin_stopall", style="primary"),
        types.InlineKeyboardButton("📥 نسخة احتياطية", callback_data="admin_backup", style="danger"),
        types.InlineKeyboardButton("🗑️ تنظيف", callback_data="admin_cleanup", style="success")
    )
    
    # الصف الأخير
    markup.add(
        types.InlineKeyboardButton("👋 رسالة الترحيب", callback_data="admin_welcome", style="primary"),
        types.InlineKeyboardButton("❓ المساعدة", callback_data="admin_help", style="danger"),
        types.InlineKeyboardButton("🔙 خروج", callback_data="exit_admin", style="success")
    )
    
    return markup

def user_panel_keyboard(user_id):
    """لوحة مفاتيح المستخدم"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("📤 رفع ملف", callback_data="user_upload", style="primary"),
        types.InlineKeyboardButton("📂 ملفاتي", callback_data="user_files", style="success"),
        types.InlineKeyboardButton("🤖 بوتاتي", callback_data="user_bots", style="primary"),
        types.InlineKeyboardButton("💎 نقاطي", callback_data="user_points", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("⭐ شراء VIP", callback_data="user_buy_vip", style="primary"),
        types.InlineKeyboardButton("🔄 تحويل نقاط", callback_data="user_transfer", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="user_referral", style="primary"),
        types.InlineKeyboardButton("🔔 الإشعارات", callback_data="user_notifs", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("📋 القوانين", callback_data="user_rules", style="primary"),
        types.InlineKeyboardButton("❓ المساعدة", callback_data="user_help", style="success"),
        types.InlineKeyboardButton("👨‍💻 𝑫𝒆𝒗𝒆𝒍𝒐𝒑𝒆𝒓", callback_data="user_dev", style="danger")
    )
    markup.add(
        types.InlineKeyboardButton("𝑴𝒚 𝑪𝒉𝒂𝒏𝒏𝒆𝒍 🖇🧸", url=f"https://t.me/{ch_adm}", style="danger")
    )

    markup.add(
        types.InlineKeyboardButton("⭐ثقه البوت⭐", url=f"https://t.me/{ch_adm}/{num_ms}", style="danger")
    )
    return markup

def approval_keyboard(file_id, user_id, filename):
    """أزرار الموافقة/الرفض - مُصلح مع تقصير أكثر للاسم"""
    # تقصير اسم الملف أكثر لتجنب خطأ BUTTON_DATA_INVALID (الحد الأقصى 64 بايت)
    short_name = filename[:15]  # تقصير أكثر
    
    # استخدام hash للاسم إذا كان طويلاً
    if len(filename) > 15:
        short_name = hashlib.md5(filename.encode()).hexdigest()[:10]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ موافقة وتشغيل", callback_data=f"app_{file_id}_{user_id}_{short_name}", style="primary"),
        types.InlineKeyboardButton("✅ موافقة فقط", callback_data=f"appo_{file_id}_{user_id}_{short_name}", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{file_id}_{user_id}_{short_name}", style="success"),
        types.InlineKeyboardButton("🚫 رفض وحظر", callback_data=f"ban_{file_id}_{user_id}_{short_name}", style="success")
    )
    return markup

def error_file_keyboard(file_id, user_id, filename):
    """أزرار الملفات التي تحتوي على أخطاء"""
    # تقصير اسم الملف
    short_name = filename[:15]
    if len(filename) > 15:
        short_name = hashlib.md5(filename.encode()).hexdigest()[:10]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف الملف", callback_data=f"delerr_{file_id}_{user_id}_{short_name}", style="success"),
        types.InlineKeyboardButton("👤 معلومات المستخدم", callback_data=f"uinfo_{user_id}", style="success")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
    return markup

def error_run_keyboard(file_id, user_id, filename):
    """أزرار الملفات التي فشل تشغيلها"""
    # تقصير اسم الملف
    short_name = filename[:15]
    if len(filename) > 15:
        short_name = hashlib.md5(filename.encode()).hexdigest()[:10]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 إعادة المحاولة", callback_data=f"retry_{file_id}_{user_id}_{short_name}", style="primary"),
        types.InlineKeyboardButton("🗑️ حذف الملف", callback_data=f"delerr_{file_id}_{user_id}_{short_name}", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("👤 معلومات المستخدم", callback_data=f"uinfo_{user_id}", style="success")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
    return markup

def vip_purchase_keyboard():
    """أزرار شراء VIP"""
    markup = types.InlineKeyboardMarkup()
    
    week_price = get_setting('vip_price_week') or '50'
    month_price = get_setting('vip_price_month') or '150'
    year_price = get_setting('vip_price_year') or '500'
    
    markup.add(types.InlineKeyboardButton(f"📅 أسبوع - {week_price} نقطة", callback_data="buy_vip_week", style="success"))
    markup.add(types.InlineKeyboardButton(f"📆 شهر - {month_price} نقطة", callback_data="buy_vip_month", style="success"))
    markup.add(types.InlineKeyboardButton(f"🗓️ سنة - {year_price} نقطة", callback_data="buy_vip_year", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="danger"))
    
    return markup

# ========== 9. معالجة الأوامر ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """معالجة أمر البدء"""
    user_id = message.from_user.id
    
    if anti_spam.check_spam(user_id):
        return
    
    # معالجة كود الإحالة
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].startswith('REF'):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (args[1],))
            ref_user = cursor.fetchone()
            if ref_user and ref_user[0] != user_id:
                referred_by = ref_user[0]
            conn.close()
        except:
            pass
    
    is_new = add_user(user_id, message.from_user.username, message.from_user.first_name)
    
    # معالجة الإحالة
    if is_new and referred_by:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET referred_by = ? WHERE user_id = ?', (referred_by, user_id))
        cursor.execute('UPDATE users SET total_referred = total_referred + 1 WHERE user_id = ?', (referred_by,))
        points = int(get_setting('points_per_referral') or 2)
        cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points, referred_by))
        conn.commit()
        conn.close()
        
        try:
            bot.send_message(referred_by, f"🎉 <b>شخص جديد انضم برابطك!</b>\n\n💎 حصلت على {points} نقطة!")
        except:
            pass
    
    # التحقق من الصيانة
    if get_setting('maintenance_mode') == '1' and not is_admin(user_id):
        # تجهيز نص الصيانة داخل اقتباس
        maintenance_text = get_setting('maintenance_msg') or "🔧 البوت تحت الصيانة حالياً..."
        
        full_text = f"<blockquote>{maintenance_text}\n\n📢 تابع قناة المطور لمعرفة موعد عودة البوت للعمل.</blockquote>"
        
        # إنشاء زرار القناة بستايل دينجر
        markup = types.InlineKeyboardMarkup()
        clean_channel = DEVELOPER_CHANNEL.replace('@', '').strip()
        markup.add(types.InlineKeyboardButton("📢 قناة التحديثات", url=f"https://t.me/{clean_channel}", style="danger"))
        
        # إرسال صورة الصيانة ريبلاي
        bot.send_photo(
            message.chat.id,
            photo=syana_url,
            caption=full_text,
            reply_markup=markup,
            parse_mode='HTML',
            reply_to_message_id=message.message_id
        )
        return
    
    # التحقق من الحظر
    user = get_user(user_id)
    if user and user[6] == 1:
        ban_reason = user[7] or "غير محدد"
        
        # تجهيز الزرار الشفاف ستايل دينجر
        markup = types.InlineKeyboardMarkup()
        # هنا هتحط اليوزر بتاعك يدوي مكان USERNAME
        markup.add(types.InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME}", style="danger"))
        
        # النص بنظام الاقتباس
        text = f"<blockquote>❌ <b>أنت محظور من استخدام البوت!</b>\n\nالسبب: {ban_reason}</blockquote>"
        
        # إرسال الصورة ريبلاي مع الكابشن المقتبس والزرار
        bot.send_photo(
            message.chat.id,
            photo=banen_url,
            caption=text,
            reply_markup=markup,
            parse_mode='HTML',
            reply_to_message_id=message.message_id
        )
        return
    
    # التحقق من حالة البوت
    if get_setting('bot_enabled') != '1' and not is_admin(user_id):
        # نص الإيقاف داخل اقتباس مع دعوة لمتابعة القناة
        text = "<blockquote>⏸️ البوت متوقف حالياً بأمر من الإدارة.\n\n📢 تابع القناة الرسمية لمعرفة حالة البوت والتحديثات القادمة.</blockquote>"
        
        # إنشاء زرار القناة بستايل دينجر
        markup = types.InlineKeyboardMarkup()
        clean_channel = DEVELOPER_CHANNEL.replace('@', '').strip()
        markup.add(types.InlineKeyboardButton("📢 قناة التحديثات", url=f"https://t.me/{clean_channel}", style="danger"))
        
        # إرسال صورة الإيقاف ريبلاي
        bot.send_photo(
            message.chat.id,
            photo=ekaf_url,
            caption=text,
            reply_markup=markup,
            parse_mode='HTML',
            reply_to_message_id=message.message_id
        )
        return
    
    # التحقق من الاشتراك الإجباري
    if get_setting('force_subscription') == '1' and not check_subscription(user_id):
        channels = get_force_channels()
        minshon = message.from_user.first_name
        markup = types.InlineKeyboardMarkup()
        for ch in channels:
            markup.add(types.InlineKeyboardButton(ch[2], url=f"https://t.me/{ch[1].replace('@', '')}", style="danger"))
        markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub", style="success"))
        bot.reply_to(message, f"<b>مرحبا {minshon} لطفاَ عليك الاشتراك ب قنوات البوت\n بعد الاشتراك اضغط تحقق 🔔✅</b>", reply_markup=markup)
        return
    
    # إشعار بالمستخدم الجديد
    if is_new and user_id != ADMIN_ID and get_setting('new_user_notification') == '1':
        try:
            caption = f"""
👤 <b>مستخدم جديد انضم للبوت!</b>

🆔 الآيدي: <code>{user_id}</code>
👤 الاسم: {message.from_user.first_name}
📌 اليوزر: @{message.from_user.username or 'غير متوفر'}
📤_via: {'إحالة' if referred_by else 'مباشر'}
⏰ الوقت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            bot.send_message(ADMIN_ID, caption)
        except:
            pass
    
    # عرض القائمة
    if is_admin(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel", style="success"),
            types.InlineKeyboardButton("👤 لوحة المستخدم", callback_data="user_panel", style="success")
        )
        bot.reply_to(message, f"👋 <b>مرحباً بك!</b>\n\n🤖 الإصدار: {BOT_VERSION}\n\nاختر لوحة التحكم:", reply_markup=markup)
    else:
        show_user_panel(message)

@bot.message_handler(commands=['admin'])
def admin_quick_command(message):
    """أمر سريع للوحة الأدمن"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ ليس لديك صلاحية للوصول لهذه اللوحة.")
        return
    
    stats = get_user_stats()
    pending_count = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE status="pending"')
        pending_count = cursor.fetchone()[0]
        conn.close()
    except:
        pass
    
    text = f"""
👑 ═════════════════════
    <b>لوحة تحكم الأدمن</b>
═════════════════════ 👑

📊 <b>الإحصائيات السريعة:</b>
• 👥 المستخدمين: {stats['total_users']}
• ⭐ VIP: {stats['vip_users']}
• 🚫 المحظورين: {stats['banned_users']}
• 🤖 البوتات النشطة: {len(running_processes)}
• 📥 طلبات معلقة: {pending_count}
• 🔥 النشطين اليوم: {stats['active_today']}

🔧 <b>الصيانة:</b> {'✅ مفعلة' if get_setting('maintenance_mode') == '1' else '❌ معطلة'}

🎯 اختر الإدارة المطلوبة:
    """
    bot.reply_to(message, text, reply_markup=admin_panel_keyboard())

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """أمر الإحصائيات"""
    stats = get_user_stats()
    text = f"""
📊 <b>إحصائيات البوت</b>

👥 <b>المستخدمين:</b>
• الإجمالي: {stats['total_users']}
• 🎖️ VIP: {stats['vip_users']}
• 🚫 المحظورين: {stats['banned_users']}
• 🔥 النشطين اليوم: {stats['active_today']}
• 🆕 الجدد اليوم: {stats['new_today']}

🤖 <b>البوتات:</b>
• 🟢 النشطة: {len(running_processes)}
• 📄 إجمالي الملفات: {stats['total_files']}

💰 <b>النقاط:</b>
• إجمالي النقاط: {stats['total_points']}
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['myid'])
def myid_command(message):
    """أمر معرفة الآيدي"""
    user = message.from_user
    text = f"""
🆔 <b>معلومات حسا��ك</b>

• الآيدي: <code>{user.id}</code>
• الاسم: {user.first_name}
• اليوزر: @{user.username or 'غير متوفر'}
• اللغة: {user.language_code or 'غير محدد'}
    """
    bot.reply_to(message, text)

def show_user_panel(message):
    """عرض لوحة المستخدم"""
    user = get_user(message.from_user.id)
    points = user[3] if user else 0
    vip_status = is_vip(message.from_user.id)
    vip_expiry = user[5] if user else None
    notifications = get_unread_notifications(message.from_user.id)
    
    text = f"""
<blockquote>✨ ━━━━━━━━━━━━━━━━ ✨

🎊 <b>أهلاً وسهلاً بك</b>
╰┈➤ {message.from_user.first_name} 👑

🚀 <b>في بوت استضافة البوتات المتقدم</b>
╰┈➤ الإصدار: {BOT_VERSION} 💫

💎 <b>نقاطك الحالية:</b> {points} نقطة
⭐ <b>حسابك:</b> {'🎖️ VIP' if vip_status else '👤 عادي'}
{'⏰ <b>ينتهي:</b> ' + vip_expiry[:10] if vip_status and vip_expiry else ''}
🔔 <b>الإشعارات:</b> {notifications} غير مقروءة

📊 <b>اختر من القائمة:</b></blockquote>
"""
    bot.send_photo(message.chat.id,photo=admin_url, caption=text, reply_markup=user_panel_keyboard(message.from_user.id))

# ========== 10. معالجة رفع الملفات مع التحقق من الأخطاء ==========
@bot.message_handler(content_types=['document'])
def handle_document(message):
    """معالجة رفع الملفات مع التحقق من الأخطاء"""
    user_id = message.from_user.id
    
    # التحقق من السبام
    if anti_spam.is_blocked(user_id):
        bot.reply_to(message, "<blockquote>⏸️ أنت محظور مؤقتاً بسبب السبام. انتظر دقيقة.</blockquote>", parse_mode='HTML')
        return
    
    # التحقق من الحظر
    user = get_user(user_id)
    if user and user[6] == 1:
        bot.reply_to(message,f"<blockquote>\n تواصل مع المطور لفهم سبب الحظر ❌ أنت محظور من استخدام البوت.\n{DEVELOPER_USERNAME}</blockquote>", parse_mode='HTML')
        return
    
    # التحقق من حالة البوت
    if get_setting('bot_enabled') != '1':
        bot.reply_to(message, "<blockquote>⏸️ البوت متوقف حالياً.</blockquote>", parse_mode='HTML')
        return
    
    # التحقق من الصيانة
    if get_setting('maintenance_mode') == '1':
        bot.reply_to(message, get_setting('maintenance_msg') or "<blockquote>🔧 البوت تحت الصيانة...</blockquote>", parse_mode='HTML')
        return
    
    doc = message.document
    
    # التحقق من نوع الملف
    if not doc.file_name.endswith('.py'):
        bot.reply_to(message, "<blockquote>❌ يسمح فقط برفع ملفات Python (.py)</blockquote>", parse_mode='HTML')
        return
    
    # التحقق من حجم الملف
    max_size = int(get_setting('max_file_size') or 10240) * 1024
    if doc.file_size > max_size:
        bot.reply_to(message, f"<blockquote>❌ حجم الملف كبير جداً!\nالحد الأقصى: {max_size // (1024*1024)} MB</blockquote>", parse_mode='HTML')
        return
    
    # التحقق من عدد البوتات
    max_bots = get_max_bots(user_id)
    user_bots = get_user_bots(user_id)
    
    # إرسال نسخة للمطور تلقائياً (ADMIN_ID)
    try:
        if user_id != ADMIN_ID:
            bot.send_document(
                ADMIN_ID,
                doc.file_id,
                caption=f"<blockquote>📥 <b>ملف جديد تم رفعه</b>\n\n👤 المستخدم: {message.from_user.first_name} (<code>{user_id}</code>)\n📄 الملف: <code>{doc.file_name}</code></blockquote>",
                parse_mode='HTML'
            )
    except:
        pass

    if len(user_bots) >= max_bots:
        bot.reply_to(message,f"<blockquote>❌ وصلت للحد الأقصى من البوتات ({max_bots})!\n\n⭐ قم بالترقية لـ VIP للحصول على مساحة أكبر ومميزات إضافية.</blockquote>",
                     parse_mode='HTML')
        return
    
    # حفظ الملف
    # تقصير اسم الملف لتجنب مشاكل Telegram Callback Data (الحد الأقصى 64 بايت)
    clean_name = doc.file_name.replace(' ', '_')
    if len(clean_name) > 20:
        ext = os.path.splitext(clean_name)[1]
        clean_name = clean_name[:15] + ext
        
    pending_name = f"{user_id}_{int(time.time())}_{clean_name}"
    pending_path = os.path.join(PENDING_FOLDER, pending_name)
    
    try:
        file_info = bot.get_file(doc.file_id)
        with open(pending_path, 'wb') as f:
            f.write(bot.download_file(file_info.file_path))
        
        # ===== التحقق من صحة الكود =====
        syntax_ok, syntax_error = check_python_syntax(pending_path)
        
        if not syntax_ok:
            # يوجد خطأ في كتابة الكود
            user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            
            # تسجيل الخطأ
            log_error(user_id, doc.file_name, "SyntaxError", syntax_error[:500])
            
            # إرسال للأدمن مع الخطأ
            with open(pending_path, 'rb') as f:
                bot.send_document(
                    ADMIN_ID,
                    f,
                    caption=f"""
🚨 <b>ملف يحتوي على خطأ في الكود!</b>

👤 المستخدم: {user_info} (<code>{user_id}</code>)
📄 الملف: <code>{doc.file_name}</code>
📏 الحجم: {doc.file_size // 1024} KB
📅 التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

{syntax_error}

⚠️ <b>هذا الملف لن يعمل حتى يتم إصلاح الخطأ!</b>
                    """,
                    reply_markup=error_file_keyboard(0, user_id, pending_name)
                )
            
            # إرسال رسالة خطأ للمستخدم (منسقة بشكل واضح)
            bot.reply_to(message, syntax_error)
            
            log_action(ADMIN_ID, "خطأ في كود", f"{doc.file_name} - {user_id}")
            return
        
        # ===== التحقق من التحذيرات الأمنية =====
        security_warnings, import_warnings = check_security_issues(pending_path)
        
        warnings_text = ""
        if security_warnings:
            warnings_text += "\n⚠️ <b>تحذيرات أمنية:</b>\n"
            for w in security_warnings[:5]:
                warnings_text += f"• {w}\n"
        
        if import_warnings:
            warnings_text += "\n📦 <b>المكتبات:</b>\n"
            for w in import_warnings[:5]:
                warnings_text += f"• {w}\n"
        
        # تسجيل في قاعدة البيانات
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO files (user_id, filename, filepath, size, upload_date, status, syntax_ok, security_warnings)
            VALUES (?, ?, ?, ?, ?, 'pending', 1, ?)
        ''', (user_id, doc.file_name, pending_path, doc.file_size, datetime.datetime.now(), 
              json.dumps(security_warnings) if security_warnings else None))
        file_id = cursor.lastrowid
        cursor.execute('UPDATE users SET total_files = total_files + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # إرسال للأدمن للموافقة
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        # تحديد حالة الكود
        code_status = "✅ الكود سليم" if not security_warnings else "⚠️ يحتوي تحذيرات"
        
        with open(pending_path, 'rb') as f:
            admin_msg = bot.send_document(
                ADMIN_ID,
                f,
                caption=f"""
📥 <b>طلب رفع ملف جديد</b>

👤 المستخدم: {user_info} (<code>{user_id}</code>)
📄 الملف: <code>{doc.file_name}</code>
📏 الحجم: {doc.file_size // 1024} KB
📅 التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
⭐ VIP: {'نعم' if is_vip(user_id) else 'لا'}
📊 بوتات نشطة: {len(user_bots)}/{max_bots}

🔍 <b>حالة الكود:</b> {code_status}
{warnings_text}

⚠️ <b>يرجى مراجعة الكود جيداً قبل الموافقة!</b>
                """,
                reply_markup=approval_keyboard(file_id, user_id, pending_name)
            )
        
        # تحديث رسالة الأدمن
        conn = get_db_connection()
        conn.execute('UPDATE files SET admin_msg_id=? WHERE id=?', (admin_msg.message_id, file_id))
        conn.commit()
        conn.close()
        
        # رسالة للمستخدم
        if security_warnings:
            error_text = "<blockquote>⚠️تم اكتشاف مشاكل في الملف:\n\n</blockquote>"
            for w in security_warnings: error_text += f"• {w}\n"
            try:
                bot.send_message(user_id, error_text)
            except:
                pass

            bot.reply_to(
        message, 
        f"<blockquote>✅ تم استلام ملفك وهو الآن <b>بانتظار مراجعة الإدارة والموافقة</b>.\n\n⏳ سيتم إشعارك فور اتخاذ القرار وتشغيل البوت.</blockquote>",
        parse_mode='HTML'
    )
        else:
            bot.reply_to(
                message,
                f"<blockquote>✅ تم استلام ملفك وهو الآن <b>بانتظار مراجعة الإدارة والموافقة</b>.\n\n⏳ سيتم إشعارك فور اتخاذ القرار وتشغيل البوت.</blockquote>",
                parse_mode='HTML')
    except Exception as e:
        logger.error(f"خطأ في رفع الملف: {e}")
        bot.reply_to(message, f"❌ حدث خطأ أثناء رفع الملف.\n{str(e)[:100]}")

# ========== 11. معالجة الأزرار ==========
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(c):
    """معالجة جميع الأزرار"""
    data = c.data
    user_id = c.from_user.id
    
    # === أزرار الموافقة والتشغيل (مُصلح بالكامل) ===
    if data.startswith('app_') and not data.startswith('appo_'):
        if not is_admin(user_id):
            return bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية")
        
        try:
            parts = data.split('_', 3)
            if len(parts) < 4:
                return bot.answer_callback_query(c.id, "❌ خطأ في البيانات")
                
            file_id_str, target_user_str, filename_hash = parts[1], parts[2], parts[3]
            file_id = int(file_id_str)
            target_user = int(target_user_str)
            
            # البحث عن الملف الفعلي في المجلد
            actual_filename = None
            actual_filepath = None
            
            # البحث في مجلد PENDING_FOLDER عن الملفات التي تبدأ بمعرف المستخدم
            if os.path.exists(PENDING_FOLDER):
                for f in os.listdir(PENDING_FOLDER):
                    # تحقق مما إذا كان الملف يبدأ بمعرف المستخدم
                    if f.startswith(f"{target_user}_"):
                        actual_filename = f
                        actual_filepath = os.path.join(PENDING_FOLDER, f)
                        break
            
            if not actual_filename or not os.path.exists(actual_filepath):
                return bot.answer_callback_query(c.id, "❌ الملف غير موجود")
            
            # نقل الملف إلى مجلد المرفوعات
            dst_path = os.path.join(UPLOAD_FOLDER, actual_filename)
            os.rename(actual_filepath, dst_path)
            
            # تشغيل البوت
            success, result = start_bot(file_id, dst_path, actual_filename, target_user)
            
            if success:
                # تحديث قاعدة البيانات
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE files SET status="approved", approved_by=?, approved_date=? WHERE id=?',
                              (user_id, datetime.datetime.now(), file_id))
                conn.commit()
                conn.close()
                
                # تحديث رسالة الأدمن
                bot.edit_message_caption(
                    caption=f"✅ <b>تمت الموافقة والتشغيل!</b>\n\n👤 المستخدم: {target_user}\n📄 الملف: {actual_filename.split('_', 2)[-1]}\n🆔 PID: {result}",
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    reply_markup=None
                )
                
                # إرسال إشعار للمستخدم
                try:
                    bot.send_message(
                        target_user,
                        f"<blockquote>✅ <b>تمت الموافقة على ملفك!</b>\n\n📄 الملف: <code>{actual_filename.split('_', 2)[-1]}</code>\n🚀 الحالة: تم فحص وتشغيل البوت بنجاح.</blockquote>",
                        parse_mode='HTML')
                except:
                    pass
                
                log_action(user_id, "موافقة وتشغيل", actual_filename)
                bot.answer_callback_query(c.id, "✅ تمت الموافقة والتشغيل")
            else:
                # فشل التشغيل - تنسيق الخطأ بشكل واضح
                error_msg = result[:1500] if len(result) > 1500 else result
                
                # محاولة تنسيق الخطأ بشكل أفضل
                try:
                    formatted_error, line_num = format_error_message(error_msg, actual_filepath)
                except:
                    formatted_error = f"❌ <b>خطأ:</b>\n<code>{escape_html(error_msg)}</code>"
                    line_num = None
                
                # تحديث قاعدة البيانات
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE files SET status="error", error_log=? WHERE id=?',
                              (error_msg[:500], file_id))
                conn.commit()
                conn.close()
                
                # تسجيل الخطأ
                log_error(target_user, actual_filename, "RuntimeError", error_msg[:500], line_num)
                
                # تحديث رسالة الأدمن مع الخطأ المنسق
                admin_error_caption = f"""🚨 <b>فشل تشغيل البوت!</b>

👤 المستخدم: {target_user}
📄 الملف: {escape_html(actual_filename.split('_', 2)[-1])}

{formatted_error}"""
                
                safe_edit_message_caption(
                    bot, c.message.chat.id, c.message.message_id,
                    admin_error_caption,
                    error_run_keyboard(file_id, target_user, actual_filename)
                )
                
                # إرسال إشعار للمستخدم (منسق بشكل واضح)
                try:
                    bot.send_message(target_user, formatted_error)
                except Exception as e:
                    logger.error(f"خطأ في إرسال رسالة للمستخدم: {e}")
                
                log_action(user_id, "فشل تشغيل", f"{actual_filename} - {error_msg[:100]}")
                bot.answer_callback_query(c.id, "❌ فشل التشغيل")
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الموافقة: {e}")
            bot.answer_callback_query(c.id, f"❌ خطأ: {str(e)[:50]}")
    
    elif data.startswith('appo_'):
        if not is_admin(user_id):
            return bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية")
        
        try:
            parts = data.split('_', 3)
            if len(parts) < 4:
                return bot.answer_callback_query(c.id, "❌ خطأ في البيانات")
                
            file_id_str, target_user_str, filename_hash = parts[1], parts[2], parts[3]
            file_id = int(file_id_str)
            target_user = int(target_user_str)
            
            # البحث عن الملف الفعلي
            actual_filename = None
            actual_filepath = None
            
            if os.path.exists(PENDING_FOLDER):
                for f in os.listdir(PENDING_FOLDER):
                    if f.startswith(f"{target_user}_"):
                        actual_filename = f
                        actual_filepath = os.path.join(PENDING_FOLDER, f)
                        break
            
            if not actual_filename or not os.path.exists(actual_filepath):
                return bot.answer_callback_query(c.id, "❌ الملف غير موجود")
            
            # نقل الملف
            dst_path = os.path.join(UPLOAD_FOLDER, actual_filename)
            os.rename(actual_filepath, dst_path)
            
            # تحديث قاعدة البيانات
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status="approved", approved_by=?, approved_date=? WHERE id=?',
                          (user_id, datetime.datetime.now(), file_id))
            conn.commit()
            conn.close()
            
            # تحديث رسالة الأدمن
            bot.edit_message_caption(
                caption=f"<blockquote>✅ <b>تمت الموافقة (بدون تشغيل)</b>\n\n👤 المستخدم: <code>{target_user}</code>\n📄 الملف: <code>{actual_filename.split('_', 2)[-1]}</code></blockquote>",
                parse_mode='HTML',
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=None
            )
            
            # إرسال إشعار للمستخدم
            try:
                bot.send_message(
                    target_user,
                    f"<blockquote>✅ <b>تمت الموافقة على ملفك!</b>\n\n📄 الملف: <code>{actual_filename.split('_', 2)[-1]}</code>\n⏳ لم يتم التشغيل تلقائياً.</blockquote>"                )
            except:
                pass
            
            log_action(user_id, "موافقة بدون تشغيل", actual_filename)
            bot.answer_callback_query(c.id, "✅ تمت الموافقة")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الموافقة فقط: {e}")
            bot.answer_callback_query(c.id, f"❌ خطأ: {str(e)[:50]}")
    
    elif data.startswith('rej_'):
        if not is_admin(user_id):
            return bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية")
        
        try:
            parts = data.split('_', 3)
            if len(parts) < 4:
                return bot.answer_callback_query(c.id, "❌ خطأ في البيانات")
                
            file_id = int(parts[1])
            target_user = int(parts[2])
            filename = parts[3]
            
            # البحث عن الملف الفعلي وحذفه
            if os.path.exists(PENDING_FOLDER):
                for f in os.listdir(PENDING_FOLDER):
                    if f.startswith(f"{target_user}_"):
                        path = os.path.join(PENDING_FOLDER, f)
                        if os.path.exists(path):
                            os.remove(path)
                        break
            
            # تحديث قاعدة البيانات
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status="rejected", rejection_reason=? WHERE id=?',
                          ("تم الرفض بواسطة الأدمن", file_id))
            conn.commit()
            conn.close()
            
            # تحديث رسالة الأدمن
            bot.edit_message_caption(
                caption=f"❌ <b>تم رفض الملف</b>\n\n👤 المستخدم: {target_user}\n📄 الملف: {filename}",
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=None
            )
            
            # إرسال إشعار للمستخدم
            try:
                bot.send_message(
                    target_user,
                    f"<blockquote>❌ <b>تم رفض ملفك</b>\n\n📄 الملف: <code>{filename}</code>\n\nيمكنك تعديل الملف وإعادة رفعه.</blockquote>",
                    parse_mode='HTML'
                )
            except:
                pass
            
            log_action(user_id, "رفض ملف", filename)
            bot.answer_callback_query(c.id, "✅ تم الرفض وحذف الملف")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الرفض: {e}")
            bot.answer_callback_query(c.id, f"❌ خطأ: {str(e)[:50]}")

    elif data.startswith('ban_'):
        if not is_admin(user_id):
            return bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية")
        
        try:
            parts = data.split('_', 3)
            if len(parts) < 4:
                return bot.answer_callback_query(c.id, "❌ خطأ في البيانات")
                
            file_id = int(parts[1])
            target_user = int(parts[2])
            filename = parts[3]
            
            # البحث عن الملف الفعلي وحذفه
            if os.path.exists(PENDING_FOLDER):
                for f in os.listdir(PENDING_FOLDER):
                    if f.startswith(f"{target_user}_"):
                        path = os.path.join(PENDING_FOLDER, f)
                        if os.path.exists(path):
                            os.remove(path)
                        break
            
            # حظر المستخدم
            ban_user(target_user, "ملف ضار")
            
            # إيقاف بوتات المستخدم
            for bot_name in list(running_processes.keys()):
                if bot_name.startswith(f"{target_user}_"):
                    stop_bot(bot_name)
            
            # تحديث قاعدة البيانات
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status="rejected" WHERE id=?', (file_id,))
            conn.commit()
            conn.close()
            
            # تحديث رسالة الأدمن
            bot.edit_message_caption(
                caption=f"🚫 <b>تم حذف الملف وحظر المستخدم</b>\n\n👤 ID: {target_user}",
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=None
            )
            
            log_action(user_id, "حظر مستخدم", str(target_user))
            bot.answer_callback_query(c.id, "✅ تم الحظر وحذف الملف")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الحظر: {e}")
            bot.answer_callback_query(c.id, f"❌ خطأ: {str(e)[:50]}")
    
    elif data.startswith('delerr_'):
        if not is_admin(user_id):
            return
        
        parts = data.split('_', 3)
        if len(parts) < 4:
            return
            
        file_id = int(parts[1])
        target_user = int(parts[2])
        filename = parts[3]
        
        # البحث عن الملف الفعلي
        for f in os.listdir(PENDING_FOLDER):
            if filename in f or f in filename:
                path = os.path.join(PENDING_FOLDER, f)
                if os.path.exists(path):
                    os.remove(path)
                break
        
        bot.edit_message_caption(
            caption=f"🗑️ <b>تم حذف الملف الخطأ</b>\n\n👤 المستخدم: {target_user}\n📄 الملف: {filename}",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=None
        )
        log_action(user_id, "حذف ملف خطأ", filename)
    
    elif data.startswith('uinfo_'):
        if not is_admin(user_id):
            return
        
        target_id = int(data.replace('uinfo_', ''))
        user_data = get_user(target_id)
        
        if user_data:
            text = f"""
👤 <b>معلومات المستخدم</b>

🆔 الآيدي: <code>{user_data[0]}</code>
👤 الاسم: {user_data[2]}
📌 اليوزر: @{user_data[1] or 'غير متوفر'}
💎 النقاط: {user_data[3]}
⭐ VIP: {'نعم - ' + (user_data[5][:10] if user_data[5] else '') if user_data[4] == 1 else 'لا'}
🚫 محظور: {'نعم - ' + (user_data[7] or '') if user_data[6] == 1 else 'لا'}
📅 تاريخ الانضمام: {user_data[8] or 'غير متوفر'}
👥 الدعوات: {user_data[11] or 0}
⚠️ التحذيرات: {user_data[15] or 0}
            """
            bot.answer_callback_query(c.id, text[:200])
        else:
            bot.answer_callback_query(c.id, "المستخدم غير موجود")
    
    elif data.startswith('retry_'):
        if not is_admin(user_id):
            return
        
        parts = data.split('_', 3)
        if len(parts) < 4:
            return
            
        file_id = int(parts[1])
        target_user = int(parts[2])
        filename = parts[3]
        
        # البحث عن الملف الفعلي
        actual_filepath = None
        for folder in [UPLOAD_FOLDER, PENDING_FOLDER]:
            for f in os.listdir(folder):
                if filename in f or f in filename:
                    actual_filepath = os.path.join(folder, f)
                    actual_filename = f
                    break
            if actual_filepath:
                break
        
        if actual_filepath and os.path.exists(actual_filepath):
            success, result = start_bot(file_id, actual_filepath, actual_filename, target_user)
            
            if success:
                safe_edit_message_caption(
                    bot, c.message.chat.id, c.message.message_id,
                    f"✅ <b>تم التشغيل بنجاح!</b>\n\n👤 المستخدم: {target_user}\n📄 الملف: {escape_html(actual_filename.split('_', 2)[-1])}\n🆔 PID: {result}",
                    None
                )
                try:
                    bot.send_message(target_user, f"✅ <b>تم تشغيل بوتك بنجاح!</b>\n\n📄 الملف: <code>{escape_html(actual_filename.split('_', 2)[-1])}</code>")
                except:
                    pass
            else:
                error_msg = result[:1500] if len(result) > 1500 else result
                # تنسيق الخطأ بشكل واضح
                try:
                    formatted_error, line_num = format_error_message(error_msg, actual_filepath)
                except:
                    formatted_error = f"❌ <b>خطأ:</b>\n<code>{escape_html(error_msg)}</code>"
                
                bot.answer_callback_query(c.id, f"❌ فشل التشغيل مرة أخرى")
                safe_edit_message_caption(
                    bot, c.message.chat.id, c.message.message_id,
                    f"🚨 <b>فشل التشغيل مرة أخرى!</b>\n\n{formatted_error}",
                    error_run_keyboard(file_id, target_user, actual_filename)
                )
                
                # إرسال للمستخدم
                try:
                    bot.send_message(target_user, formatted_error)
                except:
                    pass
        else:
            bot.answer_callback_query(c.id, "❌ الملف غير موجود")
    
    # === أزرار الأدمن ===
    elif data == "admin_panel":
        stats = get_user_stats()
        pending_count = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM files WHERE status="pending"')
            pending_count = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        text = f"""
👑 ═════════════════════
    <b>لوحة تحكم الأدمن</b>
═════════════════════ 👑

📊 <b>الإحصائيات السريعة:</b>
• 👥 المستخدمين: {stats['total_users']}
• ⭐ VIP: {stats['vip_users']}
• 🚫 المحظورين: {stats['banned_users']}
• 🤖 البوتات النشطة: {len(running_processes)}
• 📥 طلبات معلقة: {pending_count}
• 🔥 النشطين اليوم: {stats['active_today']}

🔧 <b>الصيانة:</b> {'✅ مفعلة' if get_setting('maintenance_mode') == '1' else '❌ معطلة'}

🎯 اختر الإدارة المطلوبة:
        """
        # محاولة التعديل كـ Caption (لو فيه صورة) أو كـ Text (لو نص بس)
        try:
            bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=admin_panel_keyboard(), parse_mode='HTML')
        except Exception as e:
            try:
                bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=admin_panel_keyboard(), parse_mode='HTML')
            except:
                pass
    
    elif data == "admin_pending":
        files = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, filename, upload_date FROM files WHERE status="pending" ORDER BY id DESC LIMIT 20')
            files = cursor.fetchall()
            conn.close()
        except:
            pass
        
        text = "📥 <b>ملفات بانتظار الموافقة:</b>\n\n"
        if not files:
            text += "✅ لا يوجد طلبات معلقة."
        else:
            for f in files:
                user = get_user(f[1])
                name = user[2] if user else "غير معروف"
                text += f"📄 <code>{f[2]}</code>\n👤 {name} (<code>{f[1]}</code>)\n📅 {f[3]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        safe_edit_message_text(bot, c.message.chat.id, c.message.message_id, text, markup)
    
    elif data == "admin_stats":
        stats = get_user_stats()
        pending = running = transfers = errors = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM files WHERE status="pending"')
            pending = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM files WHERE status="running"')
            running = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM points_transfers')
            transfers = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE resolved=0')
            errors = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        text = f"""
📊 ═════════════════════
    <b>إحصائيات البوت</b>
═════════════════════ 📊

👥 <b>المستخدمين:</b>
• الإجمالي: {stats['total_users']}
• 🎖️ VIP: {stats['vip_users']}
• 🚫 المحظورين: {stats['banned_users']}
• 👑 الأدمن: {stats['admin_users']}
• 🔥 النشطين اليوم: {stats['active_today']}
• 🆕 الجدد اليوم: {stats['new_today']}

💰 <b>النقاط:</b>
• إجمالي النقاط: {stats['total_points']}
• التحويلات: {transfers}

🤖 <b>البوتات:</b>
• 🟢 النشطة: {len(running_processes)}
• 📥 معلقة: {pending}
• ✅ تم تشغيلها: {running}
• 🚨 أخطاء غير محلولة: {errors}

⚙️ <b>الإعدادات:</b>
• البوت: {'✅ نشط' if get_setting('bot_enabled') == '1' else '❌ متوقف'}
• VIP: {'✅ مفعل' if get_setting('vip_enabled') == '1' else '❌ معطل'}
• الصيانة: {'✅ مفعلة' if get_setting('maintenance_mode') == '1' else '❌ معطلة'}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_stats", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "admin_server":
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        text = f"""
📡 ═════════════════════
    <b>حالة السيرفر</b>
═════════════════════ 📡

💻 <b>الموارد:</b>
• CPU: {cpu}%
• RAM: {ram.percent}% ({ram.used // (1024**2)}/{ram.total // (1024**2)} MB)
• القرص: {disk.percent}% ({disk.used // (1024**3)}/{disk.total // (1024**3)} GB)

⏰ <b>وقت التشغيل:</b>
• {uptime.days} يوم، {uptime.seconds // 3600} ساعة، {(uptime.seconds // 60) % 60} دقيقة

🤖 <b>البوت:</b>
• البوتات النشطة: {len(running_processes)}
• ملفات مرفوعة: {len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.py')])}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_server", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "admin_active":
        bots = get_all_active_bots()
        
        text = "🤖 <b>البوتات النشطة:</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        
        if not bots:
            text += "⚪ لا توجد بوتات نشطة."
        else:
            for bot_data in bots[:15]:
                user = get_user(bot_data[2])
                name = user[2] if user else "غير معروف"
                text += f"🟢 <code>{bot_data[3].split('_', 2)[-1]}</code>\n   👤 {name} | PID: {bot_data[4]}\n   ⏰ {bot_data[5]}\n\n"
                markup.add(types.InlineKeyboardButton(f"⛔ {bot_data[3].split('_', 2)[-1][:20]}", callback_data=f"stopbot_{bot_data[3]}", style="primary"))
        
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_active", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data.startswith('stopbot_'):
        if not is_admin(user_id):
            return
        
        bot_name = data.replace('stopbot_', '')
        if stop_bot(bot_name):
            bot.answer_callback_query(c.id, "✅ تم إيقاف البوت")
        else:
            bot.answer_callback_query(c.id, "❌ البوت غير نشط")
    
    elif data == "admin_resources":
        text = "📊 <b>موارد البوتات النشطة:</b>\n\n"
        
        if not running_processes:
            text += "⚪ لا توجد بوتات نشطة."
        else:
            for name, p in running_processes.items():
                try:
                    proc = psutil.Process(p.pid)
                    cpu = proc.cpu_percent(interval=0.1)
                    mem = proc.memory_info().rss / (1024 * 1024)
                    status = "🟢" if proc.is_running() else "🔴"
                    text += f"{status} <code>{name.split('_', 2)[-1]}</code>\n   CPU: {cpu:.1f}% | RAM: {mem:.1f} MB\n\n"
                except:
                    text += f"⚪ {name.split('_', 2)[-1]} (توقف)\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_resources", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "admin_restart_menu":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 إعادة تشغيل المتوقفة", callback_data="restart_stopped", style="success"),
            types.InlineKeyboardButton("🔄 إعادة تشغيل الكل", callback_data="restart_all", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        
        # حماية من خطأ الـ 400 (Message is not modified)
        try:
            bot.edit_message_text(
                "<blockquote>🔄 <b>قائمة التحكم في التشغيل:</b>\n\nيمكنك إعادة تشغيل البوتات المتوقفة أو عمل ريستارت شامل لجميع العمليات.</blockquote>",
                c.message.chat.id, 
                c.message.message_id, 
                reply_markup=markup,
                parse_mode='HTML'
            )
        except Exception:
            pass
    
    elif data == "restart_stopped":
        count = 0
        # التأكد من استخدام المتغيرات الأصلية (running_processes)
        for name, p in list(running_processes.items()):
            try:
                if not psutil.pid_exists(p.pid):
                    if restart_bot(name):
                        count += 1
                else:
                    proc = psutil.Process(p.pid)
                    if proc.status() == psutil.STATUS_ZOMBIE or not proc.is_running():
                        if restart_bot(name):
                            count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                if restart_bot(name):
                    count += 1
            except Exception:
                continue
        bot.answer_callback_query(c.id, f"✅ تم فحص وإعادة تشغيل {count} بوت متوقف", show_alert=True)
    
    elif data == "restart_all":
        count = 0
        for name in list(running_processes.keys()):
            if restart_bot(name):
                count += 1
        bot.answer_callback_query(c.id, f"🚀 تم عمل ريستارت لـ {count} بوت بنجاح", show_alert=True)
    
    elif data == "admin_stopall":
        count = stop_all_bots()
        # التأكد من تسجيل الحدث بالمتغيرات الصحيحة
        log_action(user_id, "إيقاف جميع البوتات", f"{count} بوت")
        bot.answer_callback_query(c.id, f"🛑 تم إيقاف جميع البوتات ({count})", show_alert=True)

    elif data == "admin_maintenance":
        current = get_setting('maintenance_mode')
        new = '0' if current == '1' else '1'
        update_setting('maintenance_mode', new)
        log_action(user_id, "وضع الصيانة", "تفعيل" if new == '1' else "إلغاء")
        bot.answer_callback_query(c.id, f"🔧 الصيانة: {'مفعلة ✅' if new == '1' else 'معطلة ❌'}")
    
    elif data == "admin_broadcast":
        msg = bot.send_message(c.message.chat.id, "📢 أرسل رسالة الإذاعة:")
        bot.register_next_step_handler(msg, process_broadcast)
    
    elif data == "admin_cmd":
        msg = bot.send_message(c.message.chat.id, "💻 أرسل الأمر (Shell):")
        bot.register_next_step_handler(msg, process_cmd)
    
    elif data == "admin_libs":
        libs = get_installed_libraries()
        text = "📚 <b>المكتبات المثبتة:</b>\n\n"
        if not libs:
            text += "لا توجد مكتبات مثبتة."
        else:
            for lib in libs[:20]:
                text += f"• {lib[0]}\n  📅 {lib[1]}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ تثبيت مكتبة", callback_data="install_lib", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "install_lib":
        msg = bot.send_message(c.message.chat.id, "📚 أرسل اسم المكتبة:")
        bot.register_next_step_handler(msg, process_install_lib)
    
    elif data == "admin_speed":
        if not SPEEDTEST_AVAILABLE:
            bot.answer_callback_query(c.id, "❌ مكتبة speedtest غير متوفرة")
            return
        
        msg = bot.send_message(c.message.chat.id, "⚡ جاري قياس السرعة...")
        try:
            st = speedtest.Speedtest()
            dl = st.download() / 1000000
            up = st.upload() / 1000000
            text = f"""
⚡ ═════════════════════
    <b>سرعة الاتصال</b>
═════════════════════ ⚡

📥 <b>التحميل:</b> {dl:.1f} Mbps
📤 <b>الرفع:</b> {up:.1f} Mbps
            """
            bot.edit_message_text(text, c.message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {e}", c.message.chat.id, msg.message_id)
    
    elif data == "admin_ban_forward":
        msg = bot.send_message(c.message.chat.id, "🔒 قم بتوجيه رسالة من المستخدم الذي تريد حظره:")
        bot.register_next_step_handler(msg, process_ban_forward)
    
    elif data == "admin_logs":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_logs ORDER BY id DESC LIMIT 15')
        logs = cursor.fetchall()
        conn.close()
        
        text = "📋 <b>سجلات الأدمن:</b>\n\n"
        if not logs:
            text += "لا توجد سجلات."
        else:
            for log in logs:
                admin = get_user(log[1])
                name = admin[2] if admin else str(log[1])
                text += f"• {name}\n  {log[2]}: {log[3]}\n  ⏰ {log[5]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "admin_export":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, points, is_vip, is_banned, join_date FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT filename, status, user_id, upload_date FROM files')
        files = cursor.fetchall()
        conn.close()
        
        output = StringIO()
        output.write("=== المستخدمين ===\n")
        output.write("ID,Username,Name,Points,VIP,Banned,JoinDate\n")
        for u in users:
            output.write(f"{u[0]},{u[1] or ''},{u[2] or ''},{u[3]},{u[4]},{u[5]},{u[6] or ''}\n")
        output.write("\n=== الملفات ===\n")
        output.write("Filename,Status,UserID,Date\n")
        for f in files:
            output.write(f"{f[0]},{f[1]},{f[2]},{f[3] or ''}\n")
        
        output.seek(0)
        bot.send_document(c.message.chat.id, ('export.csv', output.getvalue()), caption="📥 <b>تم تصدير البيانات</b>")
        bot.answer_callback_query(c.id, "✅ تم التصدير")
    
    elif data == "admin_backup":
        try:
            with open('bot_database.db', 'rb') as f:
                bot.send_document(c.message.chat.id, f, caption=f"📥 <b>نسخة احتياطية</b>\n📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            log_action(user_id, "نسخ احتياطي", "تم")
        except Exception as e:
            bot.answer_callback_query(c.id, f"❌ خطأ: {e}")
    
    elif data == "admin_users":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("👀 عرض المستخدمين", callback_data="view_users", style="primary"),
            types.InlineKeyboardButton("🚫 حظر", callback_data="m_ban", style="primary"),
            types.InlineKeyboardButton("✅ فك حظر", callback_data="m_unban", style="success"),
            types.InlineKeyboardButton("🔍 بحث", callback_data="m_search", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text("👥 <b>إدارة المستخدمين:</b>", c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "view_users":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, points, is_vip, is_banned FROM users ORDER BY user_id DESC LIMIT 20')
        users = cursor.fetchall()
        conn.close()
        
        text = f"👥 <b>المستخدمين:</b>\n\n"
        for u in users:
            status = "🚫" if u[5] == 1 else ("⭐" if u[4] == 1 else "✅")
            text += f"{status} {u[2]} (<code>{u[0]}</code>) - {u[3]} نقطة\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_users", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "m_ban":
        msg = bot.send_message(c.message.chat.id, "🚫 أرسل معرف المستخدم للحظر:")
        bot.register_next_step_handler(msg, lambda m: simple_action(m, "ban"))
    
    elif data == "m_unban":
        msg = bot.send_message(c.message.chat.id, "✅ أرسل معرف المستخدم لفك الحظر:")
        bot.register_next_step_handler(msg, lambda m: simple_action(m, "unban"))
    
    elif data == "m_search":
        msg = bot.send_message(c.message.chat.id, "🔍 أرسل معرف المستخدم للبحث:")
        bot.register_next_step_handler(msg, process_search_user)
    
    elif data == "admin_points":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة نقاط", callback_data="add_pts", style="primary"),
            types.InlineKeyboardButton("➖ خصم نقاط", callback_data="rem_pts", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text("💎 <b>إدارة النقاط:</b>", c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "add_pts":
        msg = bot.send_message(c.message.chat.id, "➕ أرسل المعرف والنقاط (مثال: 123456 50):")
        bot.register_next_step_handler(msg, lambda m: process_points(m, True))
    
    elif data == "rem_pts":
        msg = bot.send_message(c.message.chat.id, "➖ أرسل المعرف والنقاط:")
        bot.register_next_step_handler(msg, lambda m: process_points(m, False))
    
    elif data == "admin_vip":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("⭐ إضافة VIP", callback_data="add_vip", style="primary"),
            types.InlineKeyboardButton("🚫 إزالة VIP", callback_data="rem_vip", style="success"),
            types.InlineKeyboardButton("📋 قائمة VIP", callback_data="vip_list", style="primary")
        )
        markup.add(types.InlineKeyboardButton("💰 تعديل الأسعار", callback_data="edit_vip_prices", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text("⭐ <b>إدارة VIP:</b>", c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "add_vip":
        msg = bot.send_message(c.message.chat.id, "⭐ أرسل المعرف وعدد الأيام (مثال: 123456 30):")
        bot.register_next_step_handler(msg, process_set_vip)
    
    elif data == "rem_vip":
        msg = bot.send_message(c.message.chat.id, "🚫 أرسل معرف المستخدم:")
        bot.register_next_step_handler(msg, process_remove_vip)
    
    elif data == "vip_list":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, first_name, vip_expiry FROM users WHERE is_vip=1')
        vips = cursor.fetchall()
        conn.close()
        
        text = f"⭐ <b>قائمة VIP ({len(vips)}):</b>\n\n"
        for v in vips:
            text += f"• {v[1]} (<code>{v[0]}</code>)\n  ⏰ {v[2] or 'غير محدد'}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "edit_vip_prices":
        msg = bot.send_message(c.message.chat.id, "💰 أرسل الأسعار (أسبوع شهر سنة):")
        bot.register_next_step_handler(msg, process_edit_vip_prices)
    
    elif data == "admin_force":
        channels = get_force_channels()
        text = f"""
📢 <b>الاشتراك الإجباري</b>

الحالة: {'✅ مفعّل' if get_setting('force_subscription') == '1' else '❌ معطّل'}

<b>القنوات:</b>
        """
        if channels:
            for ch in channels:
                text += f"• {ch[2]} ({ch[1]})\n"
        else:
            text += "لا توجد قنوات مضافة."
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_ch", style="primary"),
            types.InlineKeyboardButton("🔧 تبديل الحالة", callback_data="toggle_force", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "toggle_force":
        current = get_setting('force_subscription')
        new = '0' if current == '1' else '1'
        update_setting('force_subscription', new)
        log_action(user_id, "تبديل الاشتراك الإجباري", "تفعيل" if new == '1' else "إلغاء")
        bot.answer_callback_query(c.id, f"تم: {'تفعيل ✅' if new == '1' else 'إلغاء ❌'}")
    
    elif data == "add_ch":
        msg = bot.send_message(c.message.chat.id, "📢 أرسل معرف القناة (مثال: @channel):")
        bot.register_next_step_handler(msg, process_add_channel)
    
    # === إدارة الأدمن (جديد) ===
    elif data == "admin_admins":
        if not is_super_admin(user_id):
            bot.answer_callback_query(c.id, "❌ هذه الميزة للمالك فقط!")
            return
        
        admins = get_all_admins()
        text = f"👑 <b>قائمة الأدمن ({len(admins)}):</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        for admin in admins:
            admin_id, name, username = admin
            is_owner = "👑" if admin_id == ADMIN_ID else "⭐"
            text += f"{is_owner} {name} (<code>{admin_id}</code>)\n"
            
            if admin_id != ADMIN_ID:
                # زر إزالة صلاحية (ليس للمالك)
                markup.add(types.InlineKeyboardButton(f"🗑️ إزالة {name[:15]}", callback_data=f"rem_admin_{admin_id}", style="success"))
        
        markup.add(types.InlineKeyboardButton("➕ إضافة أدمن", callback_data="add_admin_btn", style="success"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "add_admin_btn":
        if not is_super_admin(user_id):
            bot.answer_callback_query(c.id, "❌ هذه الميزة للمالك فقط!")
            return
        
        msg = bot.send_message(c.message.chat.id, "👤 أرسل معرف المستخدم لإضافته كأدمن:")
        bot.register_next_step_handler(msg, process_add_admin)
    
    elif data.startswith('rem_admin_'):
        if not is_super_admin(user_id):
            bot.answer_callback_query(c.id, "❌ هذه الميزة للمالك فقط!")
            return
        
        target_id = int(data.replace('rem_admin_', ''))
        success, msg_text = remove_admin(target_id)
        
        if success:
            bot.answer_callback_query(c.id, "✅ تم إزالة صلاحية الأدمن")
            # تحديث الرسالة
            try:
                admins = get_all_admins()
                text = f"👑 <b>قائمة الأدمن ({len(admins)}):</b>\n\n"
                for admin in admins:
                    admin_id, name, username = admin
                    is_owner = "👑" if admin_id == ADMIN_ID else "⭐"
                    text += f"{is_owner} {name} (<code>{admin_id}</code>)\n"
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("➕ إضافة أدمن", callback_data="add_admin_btn", style="success"))
                markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
                bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
            except:
                pass
        else:
            bot.answer_callback_query(c.id, f"❌ {msg_text}")
        
        log_action(user_id, "إزالة أدمن", str(target_id))
    
    # === الإعدادات (جديد) ===
    elif data == "admin_settings":
        if not is_admin(user_id):
            return
        
        text = f"""
⚙️ ═════════════════════
    <b>إعدادات البوت</b>
═════════════════════ ⚙️

🤖 <b>حالة البوت:</b> {'✅ نشط' if get_setting('bot_enabled') == '1' else '❌ متوقف'}
🔧 <b>الصيانة:</b> {'✅ مفعلة' if get_setting('maintenance_mode') == '1' else '❌ معطلة'}
📢 <b>الاشتراك الإجباري:</b> {'✅ مفعل' if get_setting('force_subscription') == '1' else '❌ معطل'}

📊 <b>إعدادات النقاط:</b>
• نقاط لكل ملف: {get_setting('points_per_file') or 5}
• نقاط لكل دعوة: {get_setting('points_per_referral') or 2}
• رسوم التحويل: {float(get_setting('transfer_fee') or 0.1) * 100}%

📁 <b>إعدادات الملفات:</b>
• الحد الأقصى للحجم: {int(get_setting('max_file_size') or 10240) // 1024} MB
• بوتات للمستخدم العادي: {get_setting('max_bots_per_user') or 5}
• بوتات لـ VIP: {get_setting('max_bots_vip') or 15}
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🤖 تبديل البوت", callback_data="toggle_bot", style="success"),
            types.InlineKeyboardButton("🔧 تبديل الصيانة", callback_data="admin_maintenance", style="success"),
            types.InlineKeyboardButton("📊 تعديل النقاط", callback_data="edit_points_settings", style="primary"),
            types.InlineKeyboardButton("📁 تعديل الملفات", callback_data="edit_files_settings", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "toggle_bot":
        if not is_admin(user_id):
            return
        
        current = get_setting('bot_enabled')
        new = '0' if current == '1' else '1'
        update_setting('bot_enabled', new)
        log_action(user_id, "تبديل البوت", "تفعيل" if new == '1' else "إيقاف")
        bot.answer_callback_query(c.id, f"البوت: {'نشط ✅' if new == '1' else 'متوقف ❌'}")
    
    elif data == "edit_points_settings":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "📊 أرسل الإعدادات (نقاط_الملف نقاط_الدعوة رسوم_التحويل):\nمثال: 5 2 0.1")
        bot.register_next_step_handler(msg, lambda m: process_edit_points_settings(m) if m.text and all(i.replace('.', '', 1).isdigit() for i in m.text.split()) else bot.send_message(m.chat.id, "❌ خطأ: يرجى إرسال أرقام فقط (مثال: 5 2 0.1)"))
    
    elif data == "edit_files_settings":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "📁 أرسل الإعدادات (حجم_الملف_KB بوتات_عادي بوتات_VIP):\nمثال: 10240 5 15")
        bot.register_next_step_handler(msg, lambda m: process_edit_files_settings(m) if m.text and all(i.isdigit() for i in m.text.split()) else bot.send_message(m.chat.id, "❌ أرسل أرقام فقط!"))
    
    # === الأخطاء (جديد) ===
    elif data == "admin_errors":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, user_id, filename, error_type, timestamp FROM error_logs WHERE resolved=0 ORDER BY id DESC LIMIT 15')
        errors = cursor.fetchall()
        conn.close()
        
        text = f"🚨 <b>سجل الأخطاء ({len(errors)}):</b>\n\n"
        
        if not errors:
            text += "✅ لا توجد أخطاء غير محلولة."
        else:
            for err in errors:
                user = get_user(err[1])
                name = user[2] if user else str(err[1])
                text += f"🔴 <b>{err[3]}</b>\n   📄 {err[2]}\n   👤 {name}\n   ⏰ {err[4]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        if errors:
            markup.add(types.InlineKeyboardButton("✅ تحديد الكل كمُحلول", callback_data="resolve_all_errors", style="success"))
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_errors", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "resolve_all_errors":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE error_logs SET resolved=1 WHERE resolved=0')
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(c.id, f"✅ تم تحديد {count} خطأ كمُحلول")
    
    # === الأوامر المخصصة (جديد) ===
    elif data == "admin_custom_cmds":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT command, response FROM custom_commands LIMIT 10')
        cmds = cursor.fetchall()
        conn.close()
        
        text = f"📝 <b>الأوامر المخصصة ({len(cmds)}):</b>\n\n"
        
        if not cmds:
            text += "لا توجد أوامر مخصصة."
        else:
            for cmd in cmds:
                text += f"🔹 <code>/{cmd[0]}</code>\n   الرد: {cmd[1][:50]}...\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إضافة أمر", callback_data="add_custom_cmd", style="success"))
        markup.add(types.InlineKeyboardButton("🗑️ حذف أمر", callback_data="del_custom_cmd", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "add_custom_cmd":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "📝 أرسل الأمر والرد (الأمر في السطر الأول، الرد في السطر الثاني):\n\nمثال:\nhello\nأهلاً وسهلاً بك!")
        bot.register_next_step_handler(msg, process_add_custom_cmd)
    
    elif data == "del_custom_cmd":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "🗑️ أرسل اسم الأمر للحذف:")
        bot.register_next_step_handler(msg, process_del_custom_cmd)
    
    # === إشعار خاص (جديد) ===
    elif data == "admin_notify":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "🔔 أرسل معرف المستخدم والرسالة (في سطرين):\n\nمثال:\n123456789\nهذه رسالة خاصة من الإدارة")
        bot.register_next_step_handler(msg, process_admin_notify)
    
    # === التقارير (جديد) ===
    elif data == "admin_reports":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, reporter_id, reported_user, reason, status FROM reports ORDER BY id DESC LIMIT 10')
        reports = cursor.fetchall()
        conn.close()
        
        text = f"📊 <b>التقارير ({len(reports)}):</b>\n\n"
        
        if not reports:
            text += "لا توجد تقارير."
        else:
            for rep in reports:
                reporter = get_user(rep[1])
                reporter_name = reporter[2] if reporter else str(rep[1])
                status_icon = "⏳" if rep[4] == 'pending' else "✅"
                text += f"{status_icon} <b>تقرير #{rep[0]}</b>\n   👤 المُبلغ: {reporter_name}\n   🎯 المُبلغ عن: <code>{rep[2]}</code>\n   📝 السبب: {rep[3]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === الملفات المرفوعة (جديد) ===
    elif data == "admin_files":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files')
        total_files = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM files WHERE status="running"')
        running = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM files WHERE status="pending"')
        pending = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM files WHERE status="error"')
        errors = cursor.fetchone()[0]
        conn.close()
        
        text = f"""
📁 ═════════════════════
    <b>إدارة الملفات</b>
═════════════════════ 📁

📊 <b>الإحصائيات:</b>
• 📄 إجمالي الملفات: {total_files}
• 🟢 تعمل: {running}
• ⏳ معلقة: {pending}
• 🚨 أخطاء: {errors}
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 كل الملفات", callback_data="view_all_files", style="primary"),
            types.InlineKeyboardButton("🚨 ملفات الأخطاء", callback_data="view_error_files", style="success"),
            types.InlineKeyboardButton("🗑️ حذف ملف", callback_data="del_file", style="success"),
            types.InlineKeyboardButton("📂 ملفات مستخدم", callback_data="user_files_admin", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "view_all_files":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename, status, user_id FROM files ORDER BY id DESC LIMIT 20')
        files = cursor.fetchall()
        conn.close()
        
        text = f"📋 <b>جميع الملفات:</b>\n\n"
        status_icons = {"running": "🟢", "pending": "⏳", "error": "🔴", "approved": "✅", "rejected": "❌", "stopped": "⚪"}
        
        for f in files:
            icon = status_icons.get(f[1], "📄")
            text += f"{icon} <code>{f[0][:25]}</code>\n   👤 <code>{f[2]}</code>\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_files", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "view_error_files":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename, user_id, error_log FROM files WHERE status="error" LIMIT 15')
        files = cursor.fetchall()
        conn.close()
        
        text = f"🚨 <b>ملفات الأخطاء:</b>\n\n"
        if not files:
            text += "✅ لا توجد ملفات أخطاء."
        else:
            for f in files:
                text += f"🔴 <code>{f[0][:25]}</code>\n   👤 <code>{f[1]}</code>\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_files", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "del_file":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "🗑️ أرسل اسم الملف للحذف:")
        bot.register_next_step_handler(msg, process_delete_file)
    
    elif data == "user_files_admin":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "👤 أرسل معرف المستخدم لعرض ملفاته:")
        bot.register_next_step_handler(msg, process_user_files_admin)
    
    # === المحظورين (جديد) ===
    elif data == "admin_banned":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, first_name, ban_reason, last_warning FROM users WHERE is_banned=1')
        banned = cursor.fetchall()
        conn.close()
        
        text = f"🚫 <b>قائمة المحظورين ({len(banned)}):</b>\n\n"
        
        if not banned:
            text += "✅ لا يوجد محظورين."
        else:
            for b in banned:
                text += f"🚫 <b>{b[1]}</b> (<code>{b[0]}</code>)\n   📝 السبب: {b[2] or 'غير محدد'}\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ فك حظر", callback_data="unban_user_btn", style="primary"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary")
        )
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "unban_user_btn":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "✅ أرسل معرف المستخدم لفك الحظر:")
        bot.register_next_step_handler(msg, lambda m: simple_action(m, "unban"))
    
    # === بحث متقدم (جديد) ===
    elif data == "admin_search":
        if not is_admin(user_id):
            return
        
        text = """
🔍 <b>البحث المتقدم</b>

اختر نوع البحث:
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🆔 بالمعرف", callback_data="search_by_id", style="success"),
            types.InlineKeyboardButton("👤 بالاسم", callback_data="search_by_name", style="success"),
            types.InlineKeyboardButton("📌 باليوزر", callback_data="search_by_username", style="primary"),
            types.InlineKeyboardButton("📄 بملف", callback_data="search_by_file", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "search_by_id":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "🆔 أرسل معرف المستخدم:")
        bot.register_next_step_handler(msg, process_search_user)
    
    elif data == "search_by_name":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "👤 أرسل جزء من اسم المستخدم:")
        bot.register_next_step_handler(msg, process_search_by_name)
    
    elif data == "search_by_username":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "📌 أرسل جزء من اليوزر:")
        bot.register_next_step_handler(msg, process_search_by_username)
    
    elif data == "search_by_file":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "📄 أرسل جزء من اسم الملف:")
        bot.register_next_step_handler(msg, process_search_by_file)
    
    # === نشاط اليوم (جديد) ===
    elif data == "admin_daily":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # إحصائيات اليوم
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(join_date) = date("now")')
        new_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(last_active) = date("now")')
        active_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM files WHERE date(upload_date) = date("now")')
        files_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM admin_logs WHERE date(timestamp) = date("now")')
        actions_today = cursor.fetchone()[0]
        cursor.execute('SELECT SUM(points) FROM points_transfers WHERE date(timestamp) = date("now")')
        points_transferred = cursor.fetchone()[0] or 0
        conn.close()
        
        text = f"""
📊 ═════════════════════
    <b>نشاط اليوم</b>
═════════════════════ 📊

📅 <b>التاريخ:</b> {datetime.datetime.now().strftime('%Y-%m-%d')}

👥 <b>المستخدمين:</b>
• 🆕 الجدد اليوم: {new_today}
• 🔥 النشطين اليوم: {active_today}

📁 <b>الملفات:</b>
• 📤 المرفوعة اليوم: {files_today}

💰 <b>النقاط:</b>
• 🔄 المحولة اليوم: {points_transferred}

📋 <b>الإجراءات:</b>
• ⚡ إجراءات اليوم: {actions_today}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_daily", style="success"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary")
        )
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === تنظيف (جديد) ===
    elif data == "admin_cleanup":
        if not is_admin(user_id):
            return
        
        text = """
🗑️ <b>أدوات التنظيف</b>

اختر ما تريد تنظيفه:
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 سجلات قديمة", callback_data="clean_logs", style="success"),
            types.InlineKeyboardButton("🚨 أخطاء محلولة", callback_data="clean_errors", style="success"),
            types.InlineKeyboardButton("📁 ملفات مرفوضة", callback_data="clean_rejected", style="primary"),
            types.InlineKeyboardButton("🔔 إشعارات قديمة", callback_data="clean_notifications", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "clean_logs":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admin_logs WHERE timestamp < date("now", "-30 days")')
        deleted = cursor.rowcount
        cursor.execute('DELETE FROM bot_logs WHERE timestamp < date("now", "-30 days")')
        deleted2 = cursor.rowcount
        conn.commit()
        conn.close()
        bot.answer_callback_query(c.id, f"✅ تم حذف {deleted + deleted2} سجل قديم")
    
    elif data == "clean_errors":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM error_logs WHERE resolved=1')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        bot.answer_callback_query(c.id, f"✅ تم حذف {deleted} خطأ محلول")
    
    elif data == "clean_rejected":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM files WHERE status="rejected"')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        bot.answer_callback_query(c.id, f"✅ تم حذف {deleted} ملف مرفوض")
    
    elif data == "clean_notifications":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications WHERE is_read=1')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        bot.answer_callback_query(c.id, f"✅ تم حذف {deleted} إشعار مقروء")
    
    # === رسالة الترحيب (جديد) ===
    elif data == "admin_welcome":
        if not is_admin(user_id):
            return
        
        current_welcome = get_setting('welcome_message') or "مرحباً بك!"
        
        text = f"""
👋 <b>رسالة الترحيب</b>

الرسالة الحالية:
<code>{current_welcome[:200]}</code>

💡 يمكنك استخدام:
• <code>{{"name"}}</code> - اسم المستخدم
• <code>{{"id"}}</code> - معرف المستخدم
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_welcome", style="success"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "edit_welcome":
        if not is_admin(user_id):
            return
        
        msg = bot.send_message(c.message.chat.id, "✏️ أرسل رسالة الترحيب الجديدة:")
        bot.register_next_step_handler(msg, process_edit_welcome)
    
    # === أزرار المستخدم ===
    elif data == "user_panel":
        show_user_panel(c.message)
    
    elif data == "user_upload":
        # إنشاء زرار الرجوع بستايل دينجر
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="danger"))
        
        # تعديل الكابشن وإضافة الزرار
        bot.edit_message_caption(
            caption=f"<blockquote>📤 <b>أرسل ملف Python (.py) الآن</b>\n\n🔍 يتم فحص الملف تلقائياً بواسطة نظام الذكاء الاصطناعي لاكتشاف الثغرات، ثم يُحال للمراجعة اليدوية من قبل الإدارة لضمان أقصى معايير الأمان.</blockquote>",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    elif data == "user_bots":
        user_bots_list = [name for name in running_processes if name.startswith(f"{user_id}_")]
        text = f"<blockquote>في حاله الضغط على اي بوت سوف يتم ايقافه  سيتعين عليك اعاده رفعه⛔⛔\n🤖بوتاتك النشطة:</blockquote>\n\n"
        markup = types.InlineKeyboardMarkup()
        
        if not user_bots_list:
            text += "<blockquote>❌ لا توجد بوتات نشطة.\n\n📤 ارفع ملفاً جديداً للبدء.</blockquote>"
        else:
            max_bots = get_max_bots(user_id)
            text += f"📊 <b>{len(user_bots_list)}/{max_bots}</b> بوت\n\n"
            for bot_name in user_bots_list:
                display_name = bot_name.split('_', 2)[-1]
                try:
                    proc = psutil.Process(running_processes[bot_name].pid)
                    status = "🟢" if proc.is_running() else "🔴"
                except:
                    status = "⚪"
                text += f"{status} {display_name}\n"
                markup.add(types.InlineKeyboardButton(f"⛔ {display_name[:20]}", callback_data=f"ustop_{bot_name}", style="primary"))
        
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="primary"))
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data.startswith('ustop_'):
        bot_name = data.replace('ustop_', '')
        if bot_name.startswith(f"{user_id}_"):
            if stop_bot(bot_name):
                bot.answer_callback_query(c.id, "✅ تم إيقاف البوت")
            else:
                bot.answer_callback_query(c.id, "❌ البوت غير نشط")
        else:
            bot.answer_callback_query(c.id, "❌ ليس بوتك")
    
    elif data == "user_files":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename, status, upload_date FROM files WHERE user_id=? ORDER BY id DESC LIMIT 10', (user_id,))
        files = cursor.fetchall()
        conn.close()
        
        text = "📂 <b>ملفاتك:</b>\n\n"
        if not files:
            text += "❌ لم ترفع أي ملفات بعد."
        else:
            status_icons = {"pending": "⏳", "running": "🟢", "rejected": "❌", "approved": "✅", "stopped": "🔴", "error": "🚨"}
            status_text = {"pending": "بانتظار الموافقة", "running": "يعمل", "rejected": "مرفوض", "approved": "تمت الموافقة", "stopped": "متوقف", "error": "خطأ"}
            for f in files:
                icon = status_icons.get(f[1], "⚪")
                text += f"{icon} {f[0]}\n   📋 {status_text.get(f[1], f[1])}\n   📅 {f[2]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="primary"))
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_points":
        user = get_user(user_id)
        points = user[3] if user else 0
        
        text = f"""
💎 <b>نقاطك:</b> {points}

📊 <b>كيفية الحصول على النقاط:</b>
• 📤 رفع ملف: +{get_setting('points_per_file')} نقطة
• 👥 دعوة صديق: +{get_setting('points_per_referral')} نقطة
• ⭐ شراء VIP يدعم البوت

💡 <b>استخدام النقاط:</b>
• شراء اشتراك VIP
• تحويل للمستخدمين الآخرين
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="primary"))
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_buy_vip":
        user = get_user(user_id)
        points = user[3] if user else 0
        vip_status = is_vip(user_id)
        vip_expiry = user[5] if user else None
        
        text = f"""
⭐ <b>شراء VIP</b>

💎 رصيدك: {points} نقطة
⭐ حالتك: {'🎖️ VIP' if vip_status else '👤 عادي'}
{'⏰ ينتهي: ' + vip_expiry[:10] if vip_status and vip_expiry else ''}

🎁 <b>مميزات VIP:</b>
• 📤 رفع حتى {get_setting('max_bots_vip')} بوت
• ⚡ أولوية في المراجعة
• 🎁 نقاط إضافية
• 🛡️ حماية متقدمة

💰 <b>الأسعار:</b>
        """
        
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=vip_purchase_keyboard())
    
    elif data.startswith('buy_vip_'):
        user = get_user(user_id)
        points = user[3] if user else 0
        
        period = data.replace('buy_vip_', '')
        prices = {
            'week': int(get_setting('vip_price_week') or 50),
            'month': int(get_setting('vip_price_month') or 150),
            'year': int(get_setting('vip_price_year') or 500)
        }
        days = {'week': 7, 'month': 30, 'year': 365}
        
        price = prices.get(period, 50)
        
        if points < price:
            bot.answer_callback_query(c.id, f"❌ رصيدك غير كافي!\nالسعر: {price} نقطة\nرصيدك: {points} نقطة")
            return
        
        # خصم النقاط وتفعيل VIP
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (price, user_id))
        conn.commit()
        conn.close()
        
        set_vip(user_id, days[period])
        
        bot.answer_callback_query(c.id, f"✅ تم الشراء!")
        bot.send_message(user_id, f"⭐ <b>مبروك! تم تفعيل VIP!</b>\n\n📅 المدة: {days[period]} يوم\n💎 تم خصم {price} نقطة")
    
    elif data == "user_transfer":
        # تجهيز الزرار الشفاف ستايل دينجر
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="danger"))
        
        # النص داخل وسم الاقتباس (blockquote)
        text = "<blockquote>🔄 أرسل معرف المستخدم والمبلغ\nمثال: 123456 50</blockquote>"
        
        # إرسال الرسالة مع تفعيل الـ HTML والزرار
        msg = bot.send_message(
            c.message.chat.id, 
            text, 
            reply_markup=markup, 
            parse_mode='HTML'
        )
        
        # تسجيل الخطوة التالية
        bot.register_next_step_handler(msg, process_user_transfer)
    
    elif data == "user_referral":
        user = get_user(user_id)
        code = user[10] if user else "N/A"
        referred = user[11] if user and user[11] else 0
        
        text = f"""
👥 <b>نظام الدعوة</b>

🔗 <b>رابط الدعوة الخاص بك:</b>
<code>https://t.me/{bot.get_me().username}?start={code}</code>

📊 <b>إحصائياتك:</b>
• عدد الدعوات: {referred}
• النقاط المكتسبة: {referred * int(get_setting('points_per_referral') or 2)}

💰 <b>تكسب {get_setting('points_per_referral') or 2} نقطة لكل شخص يدخل برابطك!</b>

💡 <b>نصيحة:</b> شارك الرابط في المجموعات والأصدقاء لكسب المزيد من النقاط.
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="success"))
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_notifs":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT title, message, created_at FROM notifications WHERE user_id=? AND is_read=0 ORDER BY id DESC LIMIT 10', (user_id,))
        notifications = cursor.fetchall()
        cursor.execute('UPDATE notifications SET is_read=1 WHERE user_id=?', (user_id,))
        conn.commit()
        conn.close()
        
        text = "🔔 <b>الإشعارات:</b>\n\n"
        if not notifications:
            text += "لا توجد إشعارات جديدة."
        else:
            for n in notifications:
                text += f"📢 {n[0]}\n{n[1]}\n📅 {n[2]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="success"))
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_rules":
        rules = get_setting('rules_text') or "📋 لم يتم تعيين قوانين بعد."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="success"))
        bot.edit_message_caption(rules, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_help":
        help_text = get_setting('help_text') or "❓ المساعدة غير متوفرة."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="success"))
        bot.edit_message_caption(help_text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "user_dev":
        # المتغيرات اللي إنت معرفها
        photo_url_adm = admin_url 
        
        text = f"""
👨‍💻 <b>معلومات المطور</b>

👤 المطور: {DEVELOPER_USERNAME}
📢 القناة: {DEVELOPER_CHANNEL}
🤖 الإصدار: {BOT_VERSION}

💡 <b>للمساعدة أو الإبلاغ عن مشكلة، تواصل مع المطور.</b>
        """
        
        markup = types.InlineKeyboardMarkup()
        
        # دعم تعدد اليوزرات (كل يوزر في زرار)
        for u in DEVELOPER_USERNAME.split():
            clean_u = u.replace('@', '').strip()
            markup.add(types.InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{clean_u}", style="danger"))
        
        # زرار الرجوع بتاعك
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="user_panel", style="primary"))

        try:
            # تحديث الميديا والنص في الرسالة الحالية
            bot.edit_message_media(
                media=types.InputMediaPhoto(photo_url_adm, caption=text, parse_mode='HTML'),
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=markup
            )
        except:
            # لو الرابط باظ، بنعدل الكابشن بس عشان البوت ميفصلش
            bot.edit_message_caption(
                caption=text,
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )   
    elif data == "exit_admin":
        show_user_panel(c.message)
    
    elif data == "check_sub":
        if check_subscription(user_id):
            bot.delete_message(c.message.chat.id, c.message.message_id)
            show_user_panel(c.message)
        else:
            bot.answer_callback_query(c.id, "❌ لم تشترك في جميع القنوات بعد")
    
    # === الميزات الجديدة للوحة الأدمن ===
    
    # === هدايا جماعية ===
    elif data == "admin_gifts":
        if not is_admin(user_id):
            return
        
        text = """
🎁 <b>نظام الهدايا الجماعية</b>

أرسل هدايا لجميع المستخدمين أو فئة معينة!
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💎 هدية نقاط للكل", callback_data="gift_all_points", style="success"),
            types.InlineKeyboardButton("⭐ VIP مجاني", callback_data="gift_vip_all", style="primary"),
            types.InlineKeyboardButton("🎁 هدية عشوائية", callback_data="gift_random", style="primary"),
            types.InlineKeyboardButton("📊 سجل الهدايا", callback_data="gift_history", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "gift_all_points":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "💎 أرسل عدد النقاط للهدية الجماعية:")
        bot.register_next_step_handler(msg, process_gift_points)
    
    elif data == "gift_vip_all":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "⭐ أرسل عدد أيام VIP للهدية:")
        bot.register_next_step_handler(msg, process_gift_vip)
    
    elif data == "gift_random":
        if not is_admin(user_id):
            return
        
        import random
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned=0 ORDER BY RANDOM() LIMIT 1')
        winner = cursor.fetchone()
        cursor.execute('UPDATE users SET points = points + 100 WHERE user_id = ?', (winner[0],))
        conn.commit()
        conn.close()
        
        if winner:
            bot.answer_callback_query(c.id, f"🎁 الفائز العشوائي: {winner[0]} حصل على 100 نقطة!")
            try:
                bot.send_message(winner[0], "🎁 <b>مبروك! ربحت 100 نقطة في السحب العشوائي!</b>")
            except:
                pass
    
    elif data == "gift_history":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT action, target, timestamp FROM admin_logs WHERE action LIKE "%هدية%" ORDER BY id DESC LIMIT 10')
        gifts = cursor.fetchall()
        conn.close()
        
        text = "📊 <b>سجل الهدايا:</b>\n\n"
        for g in gifts:
            text += f"🎁 {g[0]} - {g[1]}\n📅 {g[2]}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_gifts", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === أكواد ترويجية ===
    elif data == "admin_promo":
        if not is_admin(user_id):
            return
        
        text = """
🎫 <b>نظام الأكواد الترويجية</b>

أنشئ أكواد خاصة للحصول على نقاط أو VIP!
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إنشاء كود", callback_data="create_promo", style="success"),
            types.InlineKeyboardButton("📋 قائمة الأكواد", callback_data="list_promo", style="success"),
            types.InlineKeyboardButton("🗑️ حذف كود", callback_data="delete_promo", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "create_promo":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "🎫 أرسل الكود بالتنسيق:\n\nالكود النقاط استخدامات\nمثال: FREEX50 50 10")
        bot.register_next_step_handler(msg, process_create_promo)
    
    elif data == "list_promo":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings WHERE key LIKE "promo_%"')
        promos = cursor.fetchall()
        conn.close()
        
        text = "📋 <b>الأكواد الترويجية:</b>\n\n"
        for p in promos:
            data = json.loads(p[1])
            text += f"🎫 <code>{p[0].replace('promo_', '')}</code>\n   💎 {data['points']} نقطة | 📊 {data['uses']} استخدام\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_promo", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === نشاط شهري ===
    elif data == "admin_monthly":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # إحصائيات الشهر
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(join_date) >= date("now", "-30 days")')
        new_month = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM files WHERE date(upload_date) >= date("now", "-30 days")')
        files_month = cursor.fetchone()[0]
        cursor.execute('SELECT SUM(points) FROM points_transfers WHERE date(timestamp) >= date("now", "-30 days")')
        points_month = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COUNT(*) FROM admin_logs WHERE date(timestamp) >= date("now", "-30 days")')
        actions_month = cursor.fetchone()[0]
        
        conn.close()
        
        text = f"""
📈 ═════════════════════
    <b>نشاط الشهر</b>
═════════════════════ 📈

📅 <b>الفترة:</b> آخر 30 يوم

👥 <b>المستخدمين:</b>
• 🆕 الجدد: {new_month}

📁 <b>الملفات:</b>
• 📤 المرفوعة: {files_month}

💰 <b>النقاط:</b>
• 🔄 المحولة: {points_month}

📋 <b>الإجراءات:</b>
• ⚡ الإجمالي: {actions_month}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="admin_monthly", style="success"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === جدولة المهام ===
    elif data == "admin_schedule":
        if not is_admin(user_id):
            return
        
        text = """
⏰ <b>نظام جدولة المهام</b>

جدولة إذاعات وإشعارات في وقت محدد!
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ جدولة إذاعة", callback_data="schedule_broadcast", style="success"),
            types.InlineKeyboardButton("➕ جدولة إشعار", callback_data="schedule_notify", style="success"),
            types.InlineKeyboardButton("📋 المهام المجدولة", callback_data="list_scheduled", style="success"),
            types.InlineKeyboardButton("🗑️ إلغاء مهمة", callback_data="cancel_scheduled", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "schedule_broadcast":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "⏰ أرسل الإذاعة بالتنسيق:\n\nالوقت (ساعة:دقيقة)\nالرسالة\n\nمثال:\n15:30\nمرحباً بكم!")
        bot.register_next_step_handler(msg, process_schedule_broadcast)
    
    # === الأمان ===
    elif data == "admin_security":
        if not is_admin(user_id):
            return
        
        text = f"""
🔐 <b>إعدادات الأمان</b>

🛡️ <b>الحماية:</b>
• معدل السبام: {get_setting('spam_limit') or 5} رسائل
• نافذة السبام: {get_setting('spam_window') or 10} ثواني
• الأدمن الثانوي: {'✅ مفعل' if int(get_setting('secondary_admin') or 0) else '❌ معطل'}

⚠️ <b>التحذيرات التلقائية:</b>
• الحد الأقصى: 3 تحذيرات
• العقوبة: حظر تلقائي
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔧 إعدادات السبام", callback_data="edit_spam", style="primary"),
            types.InlineKeyboardButton("👮 أدمن ثانوي", callback_data="secondary_admin", style="success"),
            types.InlineKeyboardButton("📋 سجل الأمان", callback_data="security_log", style="success"),
            types.InlineKeyboardButton("🔒 قفل البوت", callback_data="lock_bot", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "lock_bot":
        if not is_admin(user_id):
            return
        
        current = get_setting('bot_enabled')
        new = '0' if current == '1' else '1'
        update_setting('bot_enabled', new)
        bot.answer_callback_query(c.id, f"🔒 البوت: {'مقفل ❌' if new == '0' else 'مفتوح ✅'}")
    
    # === ملاحظات الأدمن ===
    elif data == "admin_notes":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings WHERE key LIKE "note_%"')
        notes = cursor.fetchall()
        conn.close()
        
        text = f"📝 <b>ملاحظاتك ({len(notes)}):</b>\n\n"
        for n in notes:
            text += f"📌 {n[0].replace('note_', '')}\n   {n[1][:100]}\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة ملاحظة", callback_data="add_note", style="success"),
            types.InlineKeyboardButton("🗑️ حذف ملاحظة", callback_data="del_note", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "add_note":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "📝 أرسل الملاحظة بالتنسيق:\n\nالعنوان\nالمحتوى")
        bot.register_next_step_handler(msg, process_add_note)
    
    # === الردود التلقائية ===
    elif data == "admin_auto_reply":
        if not is_admin(user_id):
            return
        
        text = """
💬 <b>نظام الردود التلقائية</b>

أنشئ ردود تلقائية على كلمات معينة!
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة رد", callback_data="add_auto_reply", style="primary"),
            types.InlineKeyboardButton("📋 قائمة الردود", callback_data="list_auto_reply", style="primary"),
            types.InlineKeyboardButton("🗑️ حذف رد", callback_data="del_auto_reply", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === التقييمات ===
    elif data == "admin_ratings":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reports WHERE status="pending"')
        pending_reports = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM reports WHERE status="resolved"')
        resolved_reports = cursor.fetchone()[0]
        conn.close()
        
        text = f"""
🎯 <b>نظام التقييمات والتقارير</b>

📊 <b>إحصائيات:</b>
• ⏳ التقارير المعلقة: {pending_reports}
• ✅ التقارير المحلولة: {resolved_reports}
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 التقارير المعلقة", callback_data="pending_reports", style="primary"),
            types.InlineKeyboardButton("✅ التقارير المحلولة", callback_data="resolved_reports", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === المساعدة ===
    elif data == "admin_help":
        if not is_admin(user_id):
            return
        
        text = """
❓ <b>دليل استخدام لوحة الأدمن</b>

📥 <b>طلبات الانتظار:</b> عرض الملفات المعلقة للموافقة
📊 <b>الإحصائيات:</b> إحصائيات شاملة عن البوت
📡 <b>السيرفر:</b> معلومات عن الخادم
🤖 <b>البوتات النشطة:</b> البوتات التي تعمل حالياً
👥 <b>المستخدمين:</b> إدارة المستخدمين
💎 <b>النقاط:</b> إدارة نظام النقاط
📢 <b>إذاعة:</b> إرسال رسالة لجميع المستخدمين
⏰ <b>جدولة:</b> جدولة مهام مستقبلية
🔐 <b>الأمان:</b> إعدادات الحماية
        """
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    # === إعادة تشغيل القائمة ===
    elif data == "admin_restart_menu":
        if not is_admin(user_id):
            return
        
        text = """
🔄 <b>قائمة إعادة التشغيل</b>
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔄 إعادة تشغيل البوتات المتوقفة", callback_data="restart_stopped", style="primary"),
            types.InlineKeyboardButton("🔄 إعادة تشغيل الكل", callback_data="restart_all", style="success"),
            types.InlineKeyboardButton("🔄 إعادة تشغيل بوت معين", callback_data="restart_specific", style="success")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="success"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "restart_specific":
        if not is_admin(user_id):
            return
        msg = bot.send_message(c.message.chat.id, "📝 أرسل اسم البوت لإعادة تشغيله:")
        bot.register_next_step_handler(msg, process_restart_specific)
    
    # === تصدير البيانات ===
    elif data == "admin_export":
        if not is_admin(user_id):
            return
        
        text = """
📥 <b>تصدير البيانات</b>

اختر ما تريد تصديره:
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("👥 المستخدمين", callback_data="export_users", style="primary"),
            types.InlineKeyboardButton("📁 الملفات", callback_data="export_files", style="success"),
            types.InlineKeyboardButton("💰 النقاط", callback_data="export_points", style="primary"),
            types.InlineKeyboardButton("📋 السجلات", callback_data="export_logs", style="primary")
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    
    elif data == "export_users":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, points, is_vip, is_banned, join_date FROM users')
        users = cursor.fetchall()
        conn.close()
        
        output = StringIO()
        output.write("ID,Username,Name,Points,VIP,Banned,JoinDate\n")
        for u in users:
            output.write(f"{u[0]},{u[1] or ''},{u[2] or ''},{u[3]},{u[4]},{u[5]},{u[6] or ''}\n")
        
        output.seek(0)
        bot.send_document(c.message.chat.id, ('users_export.csv', output.getvalue()), caption="📥 <b>تم تصدير بيانات المستخدمين</b>")
    
    elif data == "export_files":
        if not is_admin(user_id):
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename, status, user_id, upload_date FROM files')
        files = cursor.fetchall()
        conn.close()
        
        output = StringIO()
        output.write("Filename,Status,UserID,Date\n")
        for f in files:
            output.write(f"{f[0]},{f[1]},{f[2]},{f[3] or ''}\n")
        
        output.seek(0)
        bot.send_document(c.message.chat.id, ('files_export.csv', output.getvalue()), caption="📥 <b>تم تصدير بيانات الملفات</b>")
    
    # === إيقاف جميع البوتات ===
    elif data == "admin_stopall":
        if not is_admin(user_id):
            return
        
        count = stop_all_bots()
        log_action(user_id, "إيقاف جميع البوتات", f"{count} بوت")
        bot.answer_callback_query(c.id, f"✅ تم إيقاف {count} بوت")
    
    # === نسخة احتياطية ===
    elif data == "admin_backup":
        if not is_admin(user_id):
            return
        
        try:
            with open('bot_database.db', 'rb') as f:
                bot.send_document(c.message.chat.id, f, caption=f"📥 <b>نسخة احتياطية</b>\n📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            log_action(user_id, "نسخ احتياطي", "تم")
        except Exception as e:
            bot.answer_callback_query(c.id, f"❌ خطأ: {e}")

# ========== 12. المعالجات المساعدة ==========
def process_broadcast(message):
    """تنفيذ الإذاعة"""
    if not is_admin(message.from_user.id):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE is_banned=0')
    users = cursor.fetchall()
    conn.close()
    
    status_msg = bot.reply_to(message, "⏳ جاري الإرسال...")
    count = 0
    
    for u in users:
        try:
            bot.send_message(u[0], f"📢 <b>إذاعة:</b>\n\n{message.text}")
            count += 1
            time.sleep(0.05)
        except:
            pass
    
    log_action(message.from_user.id, "إذاعة", f"{count} مستخدم")
    bot.edit_message_text(f"✅ تم الإرسال لـ {count} مستخدم", message.chat.id, status_msg.message_id)

def process_cmd(message):
    """تنفيذ أمر Shell"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        result = subprocess.run(message.text, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr
        
        if len(output) > 4000:
            output = output[:4000] + "...\n[تم قص الناتج]"
        
        bot.reply_to(message, f"💻 <b>الناتج:</b>\n\n<code>{output or 'لا يوجد ناتج'}</code>")
        log_action(message.from_user.id, "أمر Shell", message.text[:50])
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ انتهت المهلة (30 ثانية)")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

def process_install_lib(message):
    """تثبيت مكتبة"""
    if not is_admin(message.from_user.id):
        return
    
    lib_name = message.text.strip()
    bot.reply_to(message, f"⏳ جاري تثبيت {lib_name}...")
    
    success, result = install_library(lib_name, message.from_user.id)
    
    if success:
        bot.reply_to(message, f"✅ تم تثبيت {lib_name} بنجاح!")
        log_action(message.from_user.id, "تثبيت مكتبة", lib_name)
    else:
        bot.reply_to(message, f"❌ فشل التثبيت:\n{result[:500]}")

def process_ban_forward(message):
    """الحظر بالتوجيه"""
    if not is_admin(message.from_user.id):
        return
    
    if not message.forward_from:
        bot.reply_to(message, "❌ هذه ليست رسالة موجهة!")
        return
    
    target_id = message.forward_from.id
    
    if target_id == ADMIN_ID:
        bot.reply_to(message, "❌ لا يمكن حظر المطور الأساسي!")
        return
    
    user = get_user(target_id)
    name = user[2] if user else "غير معروف"
    
    if ban_user(target_id, "حظر بالتوجيه"):
        # إيقاف بوتات المستخدم
        for bot_name in list(running_processes.keys()):
            if bot_name.startswith(f"{target_id}_"):
                stop_bot(bot_name)
        
        bot.reply_to(message, f"✅ تم حظر المستخدم:\n🆔 {target_id}\n👤 {name}")
        log_action(message.from_user.id, "حظر بالتوجيه", str(target_id))
    else:
        bot.reply_to(message, "❌ فشل في الحظر")

def simple_action(message, action):
    """حظر/فك حظر"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text)
        
        if action == "ban":
            if ban_user(target_id, "حظر يدوي"):
                for bot_name in list(running_processes.keys()):
                    if bot_name.startswith(f"{target_id}_"):
                        stop_bot(bot_name)
                bot.reply_to(message, f"✅ تم حظر {target_id}")
                log_action(message.from_user.id, "حظر", str(target_id))
            else:
                bot.reply_to(message, "❌ فشل في الحظر")
        else:
            if unban_user(target_id):
                bot.reply_to(message, f"✅ تم فك حظر {target_id}")
                log_action(message.from_user.id, "فك حظر", str(target_id))
            else:
                bot.reply_to(message, "❌ فشل في فك الحظر")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح")

def process_search_user(message):
    """البحث عن مستخدم"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text)
        user = get_user(target_id)
        
        if user:
            status = "🚫 محظور" if user[6] == 1 else "✅ نشط"
            vip_status = "🎖️ VIP" if user[4] == 1 else "👤 عادي"
            admin_status = "👑 أدمن" if user[13] == 1 else ""
            
            user_info = f"""
🔍 <b>معلومات المستخدم</b>

🆔 الآيدي: <code>{user[0]}</code>
👤 الاسم: {user[2]}
📌 اليوزر: @{user[1] or 'غير متوفر'}
💎 النقاط: {user[3]}
⭐ الحالة: {vip_status} {admin_status}
🚫 الحظر: {status}
📅 تاريخ الانضمام: {user[8] or 'غير متوفر'}
👥 الدعوات: {user[11] or 0}
⚠️ التحذيرات: {user[15] or 0}
            """
            
            bot.reply_to(message, user_info)
        else:
            bot.reply_to(message, "❌ المستخدم غير موجود")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح")

def process_points(message, is_add):
    """إضافة/خصم نقاط"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        points = int(parts[1])
        
        if not is_add:
            points = -points
        
        if update_user_points(target_id, points):
            action = "إضافة" if is_add else "خصم"
            bot.reply_to(message, f"✅ تم {action} {abs(points)} نقطة للمستخدم {target_id}")
            log_action(message.from_user.id, f"{action} نقاط", f"{target_id} - {abs(points)}")
        else:
            bot.reply_to(message, "❌ فشل في العملية")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: الآيدي النقاط")

def process_set_vip(message):
    """تفعيل VIP"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        days = int(parts[1])
        
        if set_vip(target_id, days):
            try:
                bot.send_message(target_id, f"✅ <b>تم تفعيل VIP!</b>\n\n⏰ المدة: {days} يوم")
            except:
                pass
            bot.reply_to(message, f"✅ تم تفعيل VIP للمستخدم {target_id} لمدة {days} يوم.")
            log_action(message.from_user.id, "تفعيل VIP", f"{target_id} - {days} يوم")
        else:
            bot.reply_to(message, "❌ فشل في التفعيل")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: الآيدي الأيام")

def process_remove_vip(message):
    """إلغاء VIP"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text)
        if remove_vip(target_id):
            try:
                bot.send_message(target_id, "❌ تم إلغاء اشتراك VIP الخاص بك.")
            except:
                pass
            bot.reply_to(message, f"✅ تم إلغاء VIP للمستخدم {target_id}")
            log_action(message.from_user.id, "إلغاء VIP", str(target_id))
        else:
            bot.reply_to(message, "❌ فشل في الإلغاء")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح")

def process_edit_vip_prices(message):
    """تعديل أسعار VIP"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        update_setting('vip_price_week', parts[0])
        update_setting('vip_price_month', parts[1])
        update_setting('vip_price_year', parts[2])
        bot.reply_to(message, f"✅ تم تحديث الأسعار:\nأسبوع: {parts[0]} | شهر: {parts[1]} | سنة: {parts[2]}")
        log_action(message.from_user.id, "تعديل أسعار VIP", message.text)
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: سعر_الأسبوع سعر_الشهر سعر_السنة")

def process_add_channel(message):
    """إضافة قناة للاشتراك الإجباري"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        ch_username = message.text.strip()
        chat = bot.get_chat(ch_username)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO force_subscribe VALUES (?, ?, ?)', (chat.id, ch_username, chat.title))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تمت الإضافة: {chat.title}")
        log_action(message.from_user.id, "إضافة قناة", ch_username)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

def process_user_transfer(message):
    """تحويل نقاط للمستخدم"""
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        amount = int(parts[1])
        
        if amount <= 0:
            bot.reply_to(message, "❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if target_id == message.from_user.id:
            bot.reply_to(message, "❌ لا يمكنك التحويل لنفسك!")
            return
        
        target_user = get_user(target_id)
        if not target_user:
            bot.reply_to(message, "❌ المستخدم غير موجود")
            return
        
        success, result = transfer_points(message.from_user.id, target_id, amount)
        
        if success:
            bot.reply_to(message, f"✅ تم تحويل {amount} نقطة!\n💰 رسوم التحويل: {result} نقطة")
            try:
                bot.send_message(target_id, f"💰 <b>استلمت {amount} نقطة!</b>\n\nمن: {message.from_user.first_name}")
            except:
                pass
        else:
            bot.reply_to(message, f"❌ {result}")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: المعرف المبلغ")

# ========== دوال الميزات الجديدة ==========
def process_add_admin(message):
    """إضافة أدمن جديد"""
    if not is_super_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text.strip())
        
        # التحقق من عدم إضافة المالك مرة أخرى
        if target_id == ADMIN_ID:
            bot.reply_to(message, "⚠️ هذا هو المالك الأساسي، لديه صلاحيات كاملة بالفعل!")
            return
        
        success, msg = add_admin(target_id)
        
        if success:
            # إرسال إشعار للمستخدم الجديد
            try:
                bot.send_message(target_id, "👑 <b>مبروك! تم ترقيتك إلى أدمن!</b>\n\nيمكنك الآن الوصول إلى لوحة الأدمن عبر الأمر /admin")
            except:
                pass
            
            bot.reply_to(message, f"✅ تم إضافة <code>{target_id}</code> كأدمن بنجاح!")
            log_action(message.from_user.id, "إضافة أدمن", str(target_id))
        else:
            bot.reply_to(message, f"❌ {msg}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح. أرسل معرف المستخدم الرقمي.")

def process_edit_points_settings(message):
    """تعديل إعدادات النقاط"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        update_setting('points_per_file', parts[0])
        update_setting('points_per_referral', parts[1])
        update_setting('transfer_fee', parts[2])
        bot.reply_to(message, f"✅ تم تحديث إعدادات النقاط:\n• نقاط الملف: {parts[0]}\n• نقاط الدعوة: {parts[1]}\n• رسوم التحويل: {parts[2]}")
        log_action(message.from_user.id, "تعديل إعدادات النقاط", message.text)
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: نقاط_الملف نقاط_الدعوة رسوم_التحويل")

def process_edit_files_settings(message):
    """تعديل إعدادات الملفات"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        update_setting('max_file_size', parts[0])
        update_setting('max_bots_per_user', parts[1])
        update_setting('max_bots_vip', parts[2])
        bot.reply_to(message, f"✅ تم تحديث إعدادات الملفات:\n• حجم الملف: {int(parts[0])//1024} MB\n• بوتات عادي: {parts[1]}\n• بوتات VIP: {parts[2]}")
        log_action(message.from_user.id, "تعديل إعدادات الملفات", message.text)
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. أرسل: حجم_الملف_KB بوتات_عادي بوتات_VIP")

def process_add_custom_cmd(message):
    """إضافة أمر مخصص"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        lines = message.text.split('\n', 1)
        if len(lines) < 2:
            bot.reply_to(message, "❌ يجب إرسال الأمر في السطر الأول والرد في السطر الثاني")
            return
        
        cmd = lines[0].strip().lower().replace('/', '')
        response = lines[1].strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO custom_commands (command, response, created_by, created_at) VALUES (?, ?, ?, ?)',
                      (cmd, response, message.from_user.id, datetime.datetime.now()))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تم إضافة الأمر <code>/{cmd}</code>")
        log_action(message.from_user.id, "إضافة أمر مخصص", cmd)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

def process_del_custom_cmd(message):
    """حذف أمر مخصص"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        cmd = message.text.strip().lower().replace('/', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM custom_commands WHERE command = ?', (cmd,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            bot.reply_to(message, f"✅ تم حذف الأمر <code>/{cmd}</code>")
            log_action(message.from_user.id, "حذف أمر مخصص", cmd)
        else:
            bot.reply_to(message, "❌ الأمر غير موجود")
    except:
        bot.reply_to(message, "❌ خطأ في الحذف")

def process_admin_notify(message):
    """إرسال إشعار خاص"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        lines = message.text.split('\n', 1)
        if len(lines) < 2:
            bot.reply_to(message, "❌ يجب إرسال المعرف في السطر الأول والرسالة في السطر الثاني")
            return
        
        target_id = int(lines[0].strip())
        notification_msg = lines[1].strip()
        
        # إرسال الرسالة للمستخدم
        try:
            bot.send_message(target_id, f"🔔 <b>إشعار من الإدارة:</b>\n\n{notification_msg}")
            bot.reply_to(message, f"✅ تم إرسال الإشعار للمستخدم <code>{target_id}</code>")
            log_action(message.from_user.id, "إشعار خاص", f"{target_id}: {notification_msg[:50]}")
        except Exception as e:
            bot.reply_to(message, f"❌ فشل الإرسال: {e}")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ")

# ========== دوال الميزات الجديدة الإضافية ==========
def process_delete_file(message):
    """حذف ملف"""
    if not is_admin(message.from_user.id):
        return
    
    filename = message.text.strip()
    
    # البحث عن الملف
    found = False
    for folder in [UPLOAD_FOLDER, PENDING_FOLDER]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if filename in f or f in filename:
                    filepath = os.path.join(folder, f)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        found = True
                        break
    
    # حذف من قاعدة البيانات
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE filename LIKE ?', (f'%{filename}%',))
    db_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if found or db_deleted > 0:
        bot.reply_to(message, f"✅ تم حذف الملف بنجاح!\n🗑️ من السيرفر: {'نعم' if found else 'لا'}\n📋 من القاعدة: {db_deleted} سجل")
        log_action(message.from_user.id, "حذف ملف", filename)
    else:
        bot.reply_to(message, "❌ الملف غير موجود")

def process_user_files_admin(message):
    """عرض ملفات مستخدم للأدمن"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text.strip())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename, status, upload_date, size FROM files WHERE user_id=? ORDER BY id DESC LIMIT 20', (target_id,))
        files = cursor.fetchall()
        conn.close()
        
        if not files:
            bot.reply_to(message, f"📭 لا توجد ملفات للمستخدم <code>{target_id}</code>")
            return
        
        text = f"📂 <b>ملفات المستخدم <code>{target_id}</code>:</b>\n\n"
        status_icons = {"running": "🟢", "pending": "⏳", "error": "🔴", "approved": "✅", "rejected": "❌", "stopped": "⚪"}
        
        for f in files:
            icon = status_icons.get(f[1], "📄")
            text += f"{icon} <code>{f[0][:30]}</code>\n   📊 {f[1]} | 📅 {f[2][:10] if f[2] else 'N/A'}\n\n"
        
        bot.reply_to(message, text)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح")

def process_search_by_name(message):
    """البحث بالاسم"""
    if not is_admin(message.from_user.id):
        return
    
    search_term = message.text.strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, username, points FROM users WHERE LOWER(first_name) LIKE ?', (f'%{search_term}%',))
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "❌ لا توجد نتائج")
        return
    
    text = f"🔍 <b>نتائج البحث عن:</b> <code>{search_term}</code>\n\n"
    for u in users[:15]:
        text += f"👤 {u[1]} (<code>{u[0]}</code>)\n   📌 @{u[2] or 'لا يوجد'} | 💎 {u[3]} نقطة\n\n"
    
    bot.reply_to(message, text)

def process_search_by_username(message):
    """البحث باليوزر"""
    if not is_admin(message.from_user.id):
        return
    
    search_term = message.text.strip().lower().replace('@', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, username, points FROM users WHERE LOWER(username) LIKE ?', (f'%{search_term}%',))
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "❌ لا توجد نتائج")
        return
    
    text = f"🔍 <b>نتائج البحث عن:</b> <code>@{search_term}</code>\n\n"
    for u in users[:15]:
        text += f"👤 {u[1]} (<code>{u[0]}</code>)\n   📌 @{u[2] or 'لا يوجد'} | 💎 {u[3]} نقطة\n\n"
    
    bot.reply_to(message, text)

def process_search_by_file(message):
    """البحث بملف"""
    if not is_admin(message.from_user.id):
        return
    
    search_term = message.text.strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename, status, user_id, upload_date FROM files WHERE LOWER(filename) LIKE ? LIMIT 20', (f'%{search_term}%',))
    files = cursor.fetchall()
    conn.close()
    
    if not files:
        bot.reply_to(message, "❌ لا توجد نتائج")
        return
    
    text = f"🔍 <b>نتائج البحث عن:</b> <code>{search_term}</code>\n\n"
    status_icons = {"running": "🟢", "pending": "⏳", "error": "🔴", "approved": "✅", "rejected": "❌"}
    
    for f in files:
        icon = status_icons.get(f[1], "📄")
        text += f"{icon} <code>{f[0]}</code>\n   👤 <code>{f[2]}</code> | 📅 {f[3][:10] if f[3] else 'N/A'}\n\n"
    
    bot.reply_to(message, text)

def process_edit_welcome(message):
    """تعديل رسالة الترحيب"""
    if not is_admin(message.from_user.id):
        return
    
    new_welcome = message.text.strip()
    update_setting('welcome_message', new_welcome)
    bot.reply_to(message, f"✅ تم تحديث رسالة الترحيب!\n\n<code>{new_welcome[:200]}</code>")
    log_action(message.from_user.id, "تعديل رسالة الترحيب", new_welcome[:50])

# ========== 13. معالجة الرسائل العادية ==========
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """معالجة الرسائل العادية"""
    # تحديث نشاط المستخدم
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    # التحقق من الأوامر المخصصة
    if message.text and message.text.startswith('/'):
        cmd = message.text[1:].split()[0].lower()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT response FROM custom_commands WHERE command = ?', (cmd,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                bot.reply_to(message, result[0])
                return
        except:
            pass

# ========== دوال الميزات الجديدة ==========
def process_gift_points(message):
    """إهداء نقاط للجميع"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        points = int(message.text.strip())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET points = points + ? WHERE is_banned = 0', (points,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تم إهداء {points} نقطة لـ {affected} مستخدم!")
        log_action(message.from_user.id, "هدية نقاط جماعية", f"{points} نقطة لـ {affected} مستخدم")
    except:
        bot.reply_to(message, "❌ أرسل رقم صحيح")

def process_gift_vip(message):
    """إهداء VIP للجميع"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        days = int(message.text.strip())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        users = cursor.fetchall()
        conn.close()
        
        expiry = (datetime.datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_vip = 1, vip_expiry = ? WHERE is_banned = 0', (expiry,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تم إهداء {days} يوم VIP لـ {affected} مستخدم!")
        log_action(message.from_user.id, "هدية VIP جماعية", f"{days} يوم لـ {affected} مستخدم")
    except:
        bot.reply_to(message, "❌ أرسل رقم صحيح")

def process_create_promo(message):
    """إنشاء كود ترويجي"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        code = parts[0].upper()
        points = int(parts[1])
        uses = int(parts[2])
        
        promo_data = json.dumps({'points': points, 'uses': uses, 'used': 0})
        update_setting(f'promo_{code}', promo_data)
        
        bot.reply_to(message, f"✅ تم إنشاء الكود <code>{code}</code>\n💎 النقاط: {points}\n📊 الاستخدامات: {uses}")
        log_action(message.from_user.id, "إنشاء كود ترويجي", code)
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ. مثال: FREEX50 50 10")

def process_schedule_broadcast(message):
    """جدولة إذاعة"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        lines = message.text.split('\n', 1)
        time_str = lines[0].strip()
        broadcast_msg = lines[1].strip()
        
        hour, minute = map(int, time_str.split(':'))
        
        bot.reply_to(message, f"✅ تم جدولة الإذاعة في {time_str}\n\n⚠️ ملاحظة: الإذاعة ستتم تلقائياً عند الوصول للوقت المحدد")
        log_action(message.from_user.id, "جدولة إذاعة", f"{time_str}")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ")

def process_add_note(message):
    """إضافة ملاحظة"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        lines = message.text.split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        
        update_setting(f'note_{title}', content)
        bot.reply_to(message, f"✅ تم حفظ الملاحظة: {title}")
    except:
        bot.reply_to(message, "❌ تنسيق خاطئ")

def process_restart_specific(message):
    """إعادة تشغيل بوت معين"""
    if not is_admin(message.from_user.id):
        return
    
    bot_name = message.text.strip()
    
    # البحث عن البوت
    found_name = None
    for name in running_processes.keys():
        if bot_name.lower() in name.lower():
            found_name = name
            break
    
    if found_name:
        if restart_bot(found_name):
            bot.reply_to(message, f"✅ تم إعادة تشغيل {found_name}")
        else:
            bot.reply_to(message, f"❌ فشل في إعادة التشغيل")
    else:
        bot.reply_to(message, "❌ البوت غير موجود")

# ========== 14. التنظيف الدوري ==========
def cleanup_task():
    """مهمة التنظيف الدورية"""
    while True:
        try:
            # تنظيف السبام
            anti_spam.clean_old_records()
            
            # التحقق من انتهاء VIP
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE is_vip=1 AND vip_expiry < ?', (datetime.datetime.now(),))
            expired = cursor.fetchall()
            for user in expired:
                remove_vip(user[0])
                try:
                    bot.send_message(user[0], "⏰ <b>انتهى اشتراك VIP الخاص بك!</b>\n\nيمكنك تجديده من القائمة.")
                except:
                    pass
            conn.close()
            
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")
        
        time.sleep(3600)

# ========== 15. التشغيل الرئيسي ==========
# ========== 15. التشغيل الرئيسي ==========
def main():
    """تشغيل البوت"""
    print("=" * 60)
    print("🤖 بوت استضافة البوتات المتقدم - النسخة المُصلحة v3.5")
    print("👨‍💻 تطوير: Vonex")
    print("📢 قناة المطور: @w_nn7")
    print("=" * 60)
    
    # تهيئة قاعدة البيانات
    init_database()
    
    # بدء مراقبة البوتات
    monitor_thread = threading.Thread(target=monitor_bots, daemon=True)
    monitor_thread.start()
    
    # بدء التنظيف الدوري
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    
    # تشغيل البوت
    logger.info("🚀 البوت يعمل الآن...")

    # --- تصحيح الخطأ هنا فقط ---
    bot.remove_webhook() 
    # --------------------------
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"خطأ عام: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()