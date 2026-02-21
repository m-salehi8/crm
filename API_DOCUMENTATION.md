# مستندات API های سیستم

این مستندات شامل تمامی API های موجود در سیستم می باشد.

## فهرست مطالب

1. [Core APIs](#core-apis) - API های اصلی سیستم
2. [Chat APIs](#chat-apis) - API های چت و پیام‌رسانی
3. [Contract APIs](#contract-apis) - API های قراردادها
4. [Food APIs](#food-apis) - API های تغذیه
5. [Financial APIs](#financial-apis) - API های مالی
6. [HR APIs](#hr-apis) - API های منابع انسانی
7. [Project Management APIs](#project-management-apis) - API های مدیریت پروژه
8. [Project APIs](#project-apis) - API های پروژه‌ها

---

## Core APIs

### Authentication & User Management

#### `POST /api-auth/login/`
**توضیحات:** ورود به سیستم
**پارامترها:**
- `username` (string): نام کاربری
- `password` (string): رمز عبور

**پاسخ موفق:**
```json
{
  "token": "string"
}
```

#### `GET /get-user/`
**توضیحات:** دریافت اطلاعات کاربر جاری
**نیاز به احراز هویت:** بله

**پاسخ موفق:**
```json
{
  "id": 1,
  "username": "string",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "mobile": "string",
  "photo_url": "string",
  "thumbnail_url": "string"
}
```

#### `POST /change-password/`
**توضیحات:** تغییر رمز عبور
**نیاز به احراز هویت:** بله

**پارامترها:**
- `old` (string): رمز عبور فعلی
- `new` (string): رمز عبور جدید

#### `POST /reset-password/`
**توضیحات:** بازیابی رمز عبور
**پارامترها:**
- `username` (string): نام کاربری
- `step` (string): مرحله (1: ارسال کد، 2: تأیید کد، 3: تنظیم رمز جدید)
- `code` (string): کد تأیید (برای مرحله 2)
- `password` (string): رمز عبور جدید (برای مرحله 3)

#### `POST /user-photo-update/`
**توضیحات:** بروزرسانی عکس پروفایل
**نیاز به احراز هویت:** بله

**پارامترها:**
- `photo` (file): فایل عکس

### Departments & Units

#### `GET /department-list/`
**توضیحات:** دریافت لیست دپارتمان‌ها

**پاسخ موفق:**
```json
[
  {
    "id": 1,
    "title": "string",
    "parent": null,
    "progress": 0,
    "expected": 0
  }
]
```

#### `GET /tree-chart/{unit}/`
**توضیحات:** دریافت نمودار درختی واحد سازمانی

#### `GET /all-unit-list/`
**توضیحات:** دریافت لیست تمام واحدها

### Proclamations

#### `GET /proclamation-list/`
**توضیحات:** دریافت لیست اطلاعیه‌ها

#### `GET /proclamation-detail/{pk}/`
**توضیحات:** دریافت جزئیات اطلاعیه

#### `POST /proclamation-add-or-update/`
**توضیحات:** اضافه یا ویرایش اطلاعیه
**نیاز به احراز هویت:** بله (گروه proclamation)

### Users & Colleagues

#### `GET /my-colleague-list/`
**توضیحات:** دریافت لیست همکاران

#### `GET /all-user-list/`
**توضیحات:** دریافت لیست تمام کاربران

#### `GET /my-related-user-list/`
**توضیحات:** دریافت لیست کاربران مرتبط

### Notifications

#### `GET /my-notification-list/`
**توضیحات:** دریافت لیست اعلان‌ها

#### `POST /set-notification-seen/`
**توضیحات:** علامت‌گذاری اعلان به عنوان خوانده شده

#### `POST /remove-all-notifications/`
**توضیحات:** حذف تمام اعلان‌ها

### Settings

#### `GET /theme-list/`
**توضیحات:** دریافت لیست تم‌ها

#### `POST /set-theme/`
**توضیحات:** تنظیم تم

#### `POST /set-page-size/`
**توضیحات:** تنظیم اندازه صفحه

---

## Chat APIs

### Members & Rooms

#### `GET /chat/member-list/`
**توضیحات:** دریافت لیست اتاق‌های گفتگوی کاربر
**نیاز به احراز هویت:** بله

**پاسخ موفق:**
```json
[
  {
    "id": 1,
    "user": 1,
    "is_owner": false,
    "is_manager": false,
    "is_mute": false,
    "is_pinned": false,
    "unseen_count": 0,
    "others_last_seen_time": "string",
    "room": {
      "id": 1,
      "title": "string",
      "type": "chat",
      "logo": "string",
      "bio": "string"
    },
    "last_chat_time": "string"
  }
]
```

#### `GET /chat/member-list-item/{room}/`
**توضیحات:** دریافت اطلاعات یک اتاق گفتگو

#### `GET /chat/room-chat-list/{pk}/`
**توضیحات:** دریافت پیام‌های اتاق گفتگو

**پاسخ موفق:**
```json
{
  "old": [
    {
      "id": 1,
      "room": 1,
      "user": 1,
      "user_name": "string",
      "user_photo": "string",
      "body": "string",
      "file_url": "string",
      "send_time": "string",
      "updated": false,
      "parent": null
    }
  ],
  "new": []
}
```

#### `POST /chat/toggle-room-pin/`
**توضیحات:** سنجاق/حذف سنجاق اتاق گفتگو

**پارامترها:**
- `room` (int): شناسه اتاق

#### `GET /chat/member-detail/{pk}/`
**توضیحات:** دریافت جزئیات عضو اتاق گفتگو

---

## Contract APIs

### Agreements

#### `GET /cn/agreement-list/`
**توضیحات:** دریافت لیست قراردادها

### Contracts

#### `GET /cn/contract-list/`
**توضیحات:** دریافت لیست قراردادها
**نیاز به احراز هویت:** بله (گروه pm)

**پارامترهای Query:**
- `agreement` (int): شناسه قرارداد
- `department` (int): شناسه دپارتمان
- `need_action` (string): نیاز به اقدام (همه/منتظر اقدام)
- `from_date` (string): تاریخ شروع
- `to_date` (string): تاریخ پایان
- `type` (string): نوع قرارداد
- `genre` (string): ژانر
- `order` (string): ترتیب (تاریخ ثبت/تاریخ شروع)
- `status` (string): وضعیت
- `q` (string): جستجو

#### `GET /cn/contract-detail/{no}/`
**توضیحات:** دریافت جزئیات قرارداد

#### `POST /cn/add-contract/`
**توضیحات:** اضافه کردن قرارداد جدید

#### `POST /cn/update-contract/`
**توضیحات:** بروزرسانی قرارداد

#### `POST /cn/remove-contract/{pk}/`
**توضیحات:** حذف قرارداد

### Contract Workflow

#### `POST /cn/send-contract/`
**توضیحات:** ارسال قرارداد

#### `POST /cn/prefund-contract/`
**توضیحات:** پیش‌تأمین اعتبار قرارداد

#### `POST /cn/control-contract/`
**توضیحات:** کنترل قرارداد

#### `POST /cn/committee-contract/`
**توضیحات:** بررسی کمیته قرارداد

#### `POST /cn/accept-contract/`
**توضیحات:** تأیید قرارداد

#### `POST /cn/approve-contract/`
**توضیحات:** تصویب قرارداد

#### `POST /cn/fund-contract/`
**توضیحات:** تأمین اعتبار قرارداد

#### `POST /cn/draft-contract/`
**توضیحات:** تهیه پیش‌نویس قرارداد

#### `POST /cn/publish-contract/`
**توضیحات:** انتشار قرارداد

### Contract Parties

#### `POST /cn/add-or-update-party/`
**توضیحات:** اضافه یا ویرایش طرف قرارداد

#### `POST /cn/remove-party/`
**توضیحات:** حذف طرف قرارداد

### Payments

#### `GET /cn/pay-list/`
**توضیحات:** دریافت لیست پرداخت‌ها

#### `POST /cn/add-or-update-pay/`
**توضیحات:** اضافه یا ویرایش پرداخت

#### `POST /cn/update-pay/`
**توضیحات:** بروزرسانی پرداخت

#### `POST /cn/remove-pay/{pk}/`
**توضیحات:** حذف پرداخت

### Articles

#### `GET /cn/article-category-list/`
**توضیحات:** دریافت لیست دسته‌بندی مقالات

#### `GET /cn/article-category-detail/{pk}/`
**توضیحات:** دریافت جزئیات دسته‌بندی مقاله

#### `GET /cn/article-detail/{pk}/`
**توضیحات:** دریافت جزئیات مقاله

#### `POST /cn/article-save/`
**توضیحات:** ذخیره مقاله

#### `POST /cn/rate-article/`
**توضیحات:** امتیازدهی به مقاله

---

## Food APIs

### Foods

#### `GET /fd/food-list/`
**توضیحات:** دریافت لیست غذاها

#### `POST /fd/add-or-update-food/`
**توضیحات:** اضافه یا ویرایش غذا

#### `POST /fd/remove-food/`
**توضیحات:** حذف غذا

### Nutrition

#### `GET /fd/nutrition-list/`
**توضیحات:** دریافت لیست تغذیه

#### `GET /fd/nutrition-config/`
**توضیحات:** دریافت تنظیمات تغذیه

### Reservations

#### `GET /fd/reserve-list/`
**توضیحات:** دریافت لیست رزروها

#### `POST /fd/reserve-add-or-update/`
**توضیحات:** اضافه یا ویرایش رزرو

#### `POST /fd/reserve-update/`
**توضیحات:** بروزرسانی رزرو

#### `GET /fd/unreserved-users/{unit}/`
**توضیحات:** دریافت لیست کاربران بدون رزرو

### Food Users

#### `GET /fd/food-user-list/`
**توضیحات:** دریافت لیست کاربران غذا

#### `POST /fd/toggle-has-visitant/`
**توضیحات:** تغییر وضعیت مهمان

#### `POST /fd/toggle-has-sf-food/`
**توضیحات:** تغییر وضعیت غذای ویژه

#### `POST /fd/rate-food/`
**توضیحات:** امتیازدهی به غذا

### Visitant Requests

#### `GET /fd/visitant-lunch-request-list/`
**توضیحات:** دریافت لیست درخواست‌های ناهار مهمان

#### `POST /fd/accept-visitant-lunch-request/`
**توضیحات:** تأیید درخواست ناهار مهمان

---

## Financial APIs

### Invoice Covers

#### `GET /fn/invoice-cover-list/`
**توضیحات:** دریافت لیست جلد فاکتورها

#### `GET /fn/invoice-cover-detail/{pk}/`
**توضیحات:** دریافت جزئیات جلد فاکتور

#### `GET /fn/get-cover-pdf/{pk}/`
**توضیحات:** دریافت PDF جلد فاکتور

#### `POST /fn/add-or-update-invoice-cover/`
**توضیحات:** اضافه یا ویرایش جلد فاکتور

#### `POST /fn/remove-cover/{pk}/`
**توضیحات:** حذف جلد فاکتور

#### `POST /fn/lock-cover/`
**توضیحات:** قفل کردن جلد فاکتور

#### `POST /fn/toggle-cover-accepted/`
**توضیحات:** تغییر وضعیت تأیید جلد فاکتور

### Invoices

#### `GET /fn/invoice-category-list/`
**توضیحات:** دریافت لیست دسته‌بندی فاکتورها

#### `POST /fn/add-or-update-invoice/`
**توضیحات:** اضافه یا ویرایش فاکتور

#### `POST /fn/remove-invoice/{pk}/`
**توضیحات:** حذف فاکتور

### Invoice Users

#### `GET /fn/invoice-cover-user-list/`
**توضیحات:** دریافت لیست کاربران جلد فاکتور

#### `POST /fn/deposit-direct-invoice-cover/`
**توضیحات:** واریز مستقیم جلد فاکتور

#### `GET /fn/invoice-cover-task-list/{pk}/`
**توضیحات:** دریافت لیست وظایف جلد فاکتور

---

## HR APIs

### Work Units

#### `GET /hr/work-unit-list/`
**توضیحات:** دریافت لیست واحدهای کاری

#### `POST /hr/toggle-unit-overtime-bonus-open/`
**توضیحات:** تغییر وضعیت باز بودن اضافه کار و تشویقی

#### `POST /hr/update-unit-overtime-bonus/{pk}/`
**توضیحات:** بروزرسانی اضافه کار و تشویقی واحد

### Personnel

#### `GET /hr/personnel-list/`
**توضیحات:** دریافت لیست پرسنل

#### `GET /hr/blank-post-list/`
**توضیحات:** دریافت لیست پست‌های خالی

#### `POST /hr/update-personnel/{pk}/`
**توضیحات:** بروزرسانی پرسنل

### Works

#### `GET /hr/work-list/`
**توضیحات:** دریافت لیست کارها

#### `POST /hr/save-work/`
**توضیحات:** ذخیره کار

### Profiles & Assessments

#### `POST /hr/update-profiles/`
**توضیحات:** بروزرسانی پروفایل‌ها

#### `POST /hr/update-works/`
**توضیحات:** بروزرسانی کارها

#### `GET /hr/profile/{pk}/{year}/{month}/`
**توضیحات:** دریافت جزئیات پروفایل

#### `GET /hr/assessment-list/`
**توضیحات:** دریافت لیست ارزیابی‌ها

#### `GET /hr/assessment-detail/{pk}/`
**توضیحات:** دریافت جزئیات ارزیابی

---

## Project Management APIs

### Tasks & Jobs

#### `GET /pm/my-fellow-list/`
**توضیحات:** دریافت لیست همکاران

#### `POST /pm/update-tag-list/`
**توضیحات:** بروزرسانی لیست تگ‌ها

#### `GET /pm/task-list/`
**توضیحات:** دریافت لیست وظایف

#### `POST /pm/update-tasks-status-and-order/`
**توضیحات:** بروزرسانی وضعیت و ترتیب وظایف

#### `GET /pm/task/{pk}/`
**توضیحات:** دریافت جزئیات وظیفه

#### `POST /pm/remove-job/{pk}/`
**توضیحات:** حذف کار

#### `POST /pm/update-job/{pk}/`
**توضیحات:** بروزرسانی کار

#### `POST /pm/job-add/`
**توضیحات:** اضافه کردن کار

### Job Media & Appendices

#### `POST /pm/job-media/`
**توضیحات:** مدیریت رسانه کار

#### `POST /pm/add-job-appendix/`
**توضیحات:** اضافه کردن ضمیمه کار

#### `POST /pm/remove-job-appendix/{pk}/`
**توضیحات:** حذف ضمیمه کار

### Job Chat

#### `POST /pm/job-chat-add/`
**توضیحات:** اضافه کردن چت کار

#### `POST /pm/job-chat-remove/{pk}/`
**توضیحات:** حذف چت کار

### Task Management

#### `POST /pm/change-task-tag/`
**توضیحات:** تغییر تگ وظیفه

#### `POST /pm/job-members-change/`
**توضیحات:** تغییر اعضای کار

### Sessions

#### `GET /pm/my-session-member-list/`
**توضیحات:** دریافت لیست اعضای جلسه

#### `GET /pm/session-list-in-month/`
**توضیحات:** دریافت لیست جلسات در ماه

#### `GET /pm/session-list/`
**توضیحات:** دریافت لیست جلسات

#### `GET /pm/session-detail/{pk}/`
**توضیحات:** دریافت جزئیات جلسه

#### `POST /pm/session-add-or-update/`
**توضیحات:** اضافه یا ویرایش جلسه

#### `POST /pm/remove-session/{pk}/`
**توضیحات:** حذف جلسه

#### `POST /pm/order-session-catering/`
**توضیحات:** سفارش پذیرایی جلسه

### Rooms & Approvals

#### `GET /pm/approval-list/`
**توضیحات:** دریافت لیست تأییدها

#### `GET /pm/my-room-list/`
**توضیحات:** دریافت لیست اتاق‌های من

#### `POST /pm/overlap-check/`
**توضیحات:** بررسی تداخل

#### `GET /pm/public-room-request-list/`
**توضیحات:** دریافت لیست درخواست‌های اتاق عمومی

#### `POST /pm/public-room-request-accept/`
**توضیحات:** تأیید درخواست اتاق عمومی

### Flow & Process Management

#### `GET /pm/node-list/`
**توضیحات:** دریافت لیست گره‌ها

#### `GET /pm/node-list-excel/`
**توضیحات:** دریافت لیست گره‌ها به صورت Excel

#### `GET /pm/my-flow-pattern-list/`
**توضیحات:** دریافت لیست الگوهای جریان من

#### `GET /pm/all-flow-pattern-list/`
**توضیحات:** دریافت لیست تمام الگوهای جریان

#### `GET /pm/node/{pk}/`
**توضیحات:** دریافت جزئیات گره

#### `GET /pm/get-node-pdf/{pk}/`
**توضیحات:** دریافت PDF گره

#### `POST /pm/node-save/`
**توضیحات:** ذخیره گره

#### `POST /pm/node-remove/`
**توضیحات:** حذف گره

#### `POST /pm/node-revert/`
**توضیحات:** بازگردانی گره

#### `POST /pm/start-new-flow/{pk}/`
**توضیحات:** شروع جریان جدید

#### `GET /pm/flow-history/{pk}/`
**توضیحات:** دریافت تاریخچه جریان

### Flow Pattern Management

#### `POST /pm/flow-pattern-add/`
**توضیحات:** اضافه کردن الگوی جریان

#### `POST /pm/flow-pattern-remove/{pk}/`
**توضیحات:** حذف الگوی جریان

#### `GET /pm/flow-pattern-list/`
**توضیحات:** دریافت لیست الگوهای جریان

#### `GET /pm/flow-pattern-detail/{pk}/`
**توضیحات:** دریافت جزئیات الگوی جریان

#### `GET /pm/flow-pattern-fields/{pk}/`
**توضیحات:** دریافت فیلدهای الگوی جریان

#### `GET /pm/flow-pattern-nodes/{pk}/`
**توضیحات:** دریافت گره‌های الگوی جریان

#### `POST /pm/save-flow-pattern-detail/`
**توضیحات:** ذخیره جزئیات الگوی جریان

#### `POST /pm/save-flow-pattern-fields/`
**توضیحات:** ذخیره فیلدهای الگوی جریان

#### `POST /pm/save-flow-pattern-nodes/`
**توضیحات:** ذخیره گره‌های الگوی جریان

#### `GET /pm/post-list-for-flow-pattern-management/`
**توضیحات:** دریافت لیست پست‌ها برای مدیریت الگوی جریان

---

## Project APIs

### Missions & Projects

#### `GET /prj/mission-list/`
**توضیحات:** دریافت لیست مأموریت‌ها

#### `GET /prj/project-list/`
**توضیحات:** دریافت لیست پروژه‌ها

#### `GET /prj/project-detail/{pk}/`
**توضیحات:** دریافت جزئیات پروژه

#### `POST /prj/project-add-or-update/`
**توضیحات:** اضافه یا ویرایش پروژه

#### `POST /prj/project-remove/{pk}/`
**توضیحات:** حذف پروژه

#### `GET /prj/my-active-project-list/`
**توضیحات:** دریافت لیست پروژه‌های فعال من

#### `GET /prj/all-active-project-list/`
**توضیحات:** دریافت لیست تمام پروژه‌های فعال

#### `GET /prj/active-project-list-in-units/`
**توضیحات:** دریافت لیست پروژه‌های فعال در واحدها

### Phases

#### `POST /prj/phase-add-or-update/`
**توضیحات:** اضافه یا ویرایش فاز

#### `POST /prj/phase-remove/`
**توضیحات:** حذف فاز

#### `GET /prj/phase-report-list/{pk}/`
**توضیحات:** دریافت لیست گزارش‌های فاز

### Project Workflow

#### `POST /prj/project-confirm-or-accept/`
**توضیحات:** تأیید یا پذیرش پروژه

#### `POST /prj/project-approve/`
**توضیحات:** تصویب پروژه

### Reports

#### `GET /prj/report-list/`
**توضیحات:** دریافت لیست گزارش‌ها

#### `POST /prj/report-add/`
**توضیحات:** اضافه کردن گزارش

#### `POST /prj/report-remove/`
**توضیحات:** حذف گزارش

#### `POST /prj/report-accept/`
**توضیحات:** پذیرش گزارش

#### `POST /prj/report-approve/`
**توضیحات:** تصویب گزارش

### Allocations

#### `GET /prj/project-allocations/{pk}/`
**توضیحات:** دریافت تخصیص‌های پروژه

#### `GET /prj/allocation-list/`
**توضیحات:** دریافت لیست تخصیص‌ها

#### `GET /prj/allocate-project-list-in-department/{pk}/`
**توضیحات:** دریافت لیست پروژه‌های قابل تخصیص در دپارتمان

#### `POST /prj/add-or-update-allocation/`
**توضیحات:** اضافه یا ویرایش تخصیص

#### `POST /prj/remove-allocation/`
**توضیحات:** حذف تخصیص

### Team Management

#### `GET /prj/my-teammates/`
**توضیحات:** دریافت لیست هم‌تیمی‌ها

---

## اطلاعات عمومی

### احراز هویت
اکثر API ها نیاز به احراز هویت دارند. برای احراز هویت، توکن دریافتی از `/api-auth/login/` را در هدر `Authorization` ارسال کنید:

```
Authorization: Token your_token_here
```

### کدهای وضعیت HTTP
- `200`: موفقیت‌آمیز
- `201`: ایجاد موفقیت‌آمیز
- `400`: درخواست نامعتبر
- `401`: عدم احراز هویت
- `403`: عدم دسترسی
- `404`: یافت نشد
- `500`: خطای سرور

### فرمت تاریخ
تاریخ‌ها در سیستم به فرمت جلالی (Shamsi) ذخیره می‌شوند.

### Pagination
برای API هایی که لیست بازمی‌گردانند، از pagination استفاده می‌شود:
- `page`: شماره صفحه
- `page_size`: تعداد آیتم در هر صفحه

### فیلتر و جستجو
API های لیست معمولاً از پارامترهای زیر پشتیبانی می‌کنند:
- `q`: متن جستجو
- `ordering`: ترتیب‌بندی
- `search`: جستجو در فیلدهای مشخص

---

## نکات مهم

1. تمام API ها از RESTful design pattern پیروی می‌کنند
2. اکثر API ها نیاز به احراز هویت دارند
3. برخی API ها نیاز به دسترسی‌های خاص (groups) دارند
4. فایل‌ها و رسانه‌ها در `/media/` ذخیره می‌شوند
5. سیستم از Django REST Framework استفاده می‌کند
6. پایگاه داده از PostgreSQL استفاده می‌کند
7. تاریخ‌ها به فرمت جلالی (Shamsi) هستند

