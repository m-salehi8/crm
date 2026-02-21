import os
from pathlib import Path
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static
BASE_DIR = Path(__file__).resolve().parent.parent


core = {
    "title": "هسته سیستم",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "تم", "icon": "palette", "link": reverse_lazy("admin:core_theme_changelist")},
        {"title": "واحدهای سازمانی", "icon": "apartment", "link": reverse_lazy("admin:core_unit_changelist")},
        {"title": "پست سازمانی", "icon": "military_tech", "link": reverse_lazy("admin:core_post_changelist")},
        {"title": "کاربر", "icon": "person", "link": reverse_lazy("admin:core_user_changelist")},
        {"title": "کلید", "icon": "key", "link": reverse_lazy("admin:core_key_changelist")},
        {"title": "اطلاعیه", "icon": "campaign", "link": reverse_lazy("admin:core_proclamation_changelist")},
        {"title": "مشاهده اطلاعیه", "icon": "mark_chat_read", "link": reverse_lazy("admin:core_proclamationseen_changelist")},
        {"title": "یادآوری", "icon": "notifications_active", "link": reverse_lazy("admin:core_notification_changelist")},
        {"title": "پیامک", "icon": "sms", "link": reverse_lazy("admin:core_sms_changelist")},
        {"title": "کامپیوتر", "icon": "devices", "link": reverse_lazy("admin:core_computer_changelist")},
        {"title": "منو", "icon": "list_alt", "link": reverse_lazy("admin:core_menu_changelist")},
        {"title": "داشبورد", "icon": "dashboard", "link": reverse_lazy("admin:core_dashboard_changelist")},
        {"title": "لاگ فعالیت کاربر", "icon": "history", "link": reverse_lazy("admin:core_useractivitylog_changelist")},
        {"title": "لاگ احراز هویت کاربر", "icon": "lock_open", "link": reverse_lazy("admin:core_userauthlog_changelist")},
    ],
}

prj = {
    "title": "مدیریت پروژه",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "ماموریت", "icon": "assignment", "link": reverse_lazy("admin:prj_mission_changelist")},
        {"title": "برنامه", "icon": "precision_manufacturing", "link": reverse_lazy("admin:prj_project_changelist")},
        {"title": "تیم برنامه", "icon": "precision_manufacturing", "link": reverse_lazy("admin:prj_projectsteam_changelist")},
        {"title": "تیم فاز", "icon": "precision_manufacturing", "link": reverse_lazy("admin:prj_phaseteam_changelist")},
        {"title": "گزارش پیشرفت", "icon": "summarize", "link": reverse_lazy("admin:prj_report_changelist")},
        {"title": "لاگ بروزرسانی روزانه", "icon": "pending_actions", "link": reverse_lazy("admin:prj_dailyupdatelog_changelist")},
        {"title": "پرداخت", "icon": "connect_without_contact", "link": reverse_lazy("admin:prj_allocation_changelist")},
        {"title": "سند راهبردی", "icon": "folder_shared", "link": reverse_lazy("admin:prj_document_changelist")},
    ],
}

pm = {
    "title": "فرآیندها و جلسات",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "اتاق جلسه", "icon": "meeting_room", "link": reverse_lazy("admin:pm_room_changelist")},
        {"title": "جلسه", "icon": "event_available", "link": reverse_lazy("admin:pm_session_changelist")},
        {"title": "مصوبات جلسه", "icon": "verified_user", "link": reverse_lazy("admin:pm_approval_changelist")},
        {"title": "برچسب", "icon": "label", "link": reverse_lazy("admin:pm_tag_changelist")},
        {"title": "استثنا ارجاع", "icon": "supervisor_account", "link": reverse_lazy("admin:pm_fellowexception_changelist")},
        {"title": "کار", "icon": "task", "link": reverse_lazy("admin:pm_job_changelist")},
        {"title": "FlowPattern Type", "icon": "hub", "link": reverse_lazy("admin:pm_flowpatterntype_changelist")},
        {"title": "FlowPattern", "icon": "hub", "link": reverse_lazy("admin:pm_flowpattern_changelist")},
        {"title": "Fields", "icon": "list", "link": reverse_lazy("admin:pm_field_changelist")},
        {"title": "NodePattern", "icon": "share", "link": reverse_lazy("admin:pm_nodepattern_changelist")},
        {"title": "Dispatch", "icon": "send_and_archive", "link": reverse_lazy("admin:pm_dispatch_changelist")},
        {"title": "فرایند", "icon": "sync_alt", "link": reverse_lazy("admin:pm_flow_changelist")},
    ],
}

fd = {
    "title": "تغذیه و غذا",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "غذا", "icon": "restaurant_menu", "link": reverse_lazy("admin:fd_food_changelist")},
        {"title": "برنامه غذایی", "icon": "local_dining", "link": reverse_lazy("admin:fd_nutrition_changelist")},
        {"title": "Nutrition foods", "icon": "set_meal", "link": reverse_lazy("admin:fd_nutritionfood_changelist")},
        {"title": "رزرو غذا", "icon": "receipt_long", "link": reverse_lazy("admin:fd_reserve_changelist")},
        {"title": "انبار", "icon": "inventory", "link": reverse_lazy("admin:fd_warehouse_changelist")},
    ],
}

hr = {
    "title": "منابع انسانی",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "پروفایل", "icon": "person", "link": reverse_lazy("admin:hr_profile_changelist")},
        {"title": "کارکرد", "icon": "work", "link": reverse_lazy("admin:hr_work_changelist")},
        {"title": "ارزیابی 360 درجه", "icon": "bar_chart", "link": reverse_lazy("admin:hr_assessment_changelist")},
        {"title": "ارزیابی 360 درجه - سوال", "icon": "quiz", "link": reverse_lazy("admin:hr_question_changelist")},
        {"title": "کسورات", "icon": "money_off_csred", "link": reverse_lazy("admin:hr_deductionwork_changelist")},
        {"title": "نوع کسورات", "icon": "money_off_csred", "link": reverse_lazy("admin:hr_deductiontype_changelist")},
        {"title": "ارزیابی ماهانه - گروه ارزیابی", "icon": "groups_2", "link": reverse_lazy("admin:hr_evaluationgroup_changelist")},
        {"title": "ارزیابی ماهانه", "icon": "rule", "link": reverse_lazy("admin:hr_evaluation_changelist")},
    ],
}

cn = {
    "title": "مدیریت قراردادها",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "توافق‌نامه", "icon": "handshake", "link": reverse_lazy("admin:cn_agreement_changelist")},
        {"title": "قرارداد", "icon": "description", "link": reverse_lazy("admin:cn_contract_changelist")},
        {"title": "فازهای قرارداد", "icon": "alt_route", "link": reverse_lazy("admin:cn_step_changelist")},
        {"title": "پرداخت", "icon": "payments", "link": reverse_lazy("admin:cn_pay_changelist")},
        {"title": "مقاله - توع", "icon": "folder_open", "link": reverse_lazy("admin:cn_articlecategory_changelist")},
        {"title": "مقاله", "icon": "text_snippet", "link": reverse_lazy("admin:cn_article_changelist")},
        {"title": "مقاله - پیوست", "icon": "attachment", "link": reverse_lazy("admin:cn_articleattachment_changelist")},
        {"title": "مقاله - درخواست", "icon": "verified_user", "link": reverse_lazy("admin:cn_articlepermit_changelist")},
        {"title": "مقاله - گفتگو", "icon": "chat", "link": reverse_lazy("admin:cn_articlechat_changelist")},
        {"title": "مقاله - امتیاز", "icon": "star", "link": reverse_lazy("admin:cn_articlerate_changelist")},
    ],
}

fn = {
    "title": "امور مالی",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "روکش سند هزینه", "icon": "note_alt", "link": reverse_lazy("admin:fn_invoicecover_changelist")},
        {"title": "معین هزینه", "icon": "view_list", "link": reverse_lazy("admin:fn_invoicecategory_changelist")},
    ],
}

chat = {
    "title": "پیام‌رسان داخلی",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "اتاق گفتگو", "icon": "forum", "link": reverse_lazy("admin:chat_room_changelist")},
        {"title": "اتاق گفتگو - عضو", "icon": "group", "link": reverse_lazy("admin:chat_member_changelist")},
        {"title": "گفتگو", "icon": "message", "link": reverse_lazy("admin:chat_chat_changelist")},
    ],
}

video = {
    "title": "ویدیوها",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "ویدیو", "icon": "movie", "link": reverse_lazy("admin:video_video_changelist")},
        {"title": "لایک ویدیو", "icon": "thumb_up_alt", "link": reverse_lazy("admin:video_videolike_changelist")},
        {"title": "نظر / دیدگاه ویدیو", "icon": "message", "link": reverse_lazy("admin:video_videocomment_changelist")},
        {"title": "دسته‌بندی ویدیو", "icon": "video_label", "link": reverse_lazy("admin:video_videocategory_changelist")},
        {"title": "برچسب ویدیو", "icon": "tag", "link": reverse_lazy("admin:video_videotag_changelist")},
        {"title": "ارتباط دسته‌بندی ویدیو", "icon": "scatter_plot", "link": reverse_lazy("admin:video_videocategoryrelation_changelist")},
        {"title": "ارتباط برچسب ویدیو", "icon": "scatter_plot", "link": reverse_lazy("admin:video_videotagrelation_changelist")},
        {"title": "ضمیمه فایل ویدیو", "icon": "attach_file", "link": reverse_lazy("admin:video_videofileappendix_changelist")},
    ],
}


UNFOLD = {
    "SITE_TITLE": "پورتال سازمانی",
    "SITE_HEADER": "مدیریت پورتال",
    "SITE_SUBHEADER": "سامانه مدیریت یکپارچه",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "light",
    "DASHBOARD_CALLBACK": "backend.admin_dashboard.dashboard_callback",
    "STYLES": [
        lambda request: static("css/admin-custom.css"),
        lambda request: static("css/admin-rtl.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin-custom.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("داشبورد"),
                "separator": True,
                "items": [
                    {
                        "title": _("پیشخوان"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            core,
            hr,
            chat,
            video,
            cn,
            fn,
            pm,
            fd,
            prj,

        ],
    },
    "TABS": [
        {
            "models": [
                "pm.job",
            ],
            "items": [
                {
                    "title": _("همه وظایف"),
                    "link": reverse_lazy("admin:pm_job_changelist"),
                },
                {
                    "title": _("انجام شده"),
                    "query_params": "?status__exact=done",
                    "link": reverse_lazy("admin:pm_job_changelist"),
                },
                {
                    "title": _("در دست اقدام"),
                    "query_params": "?status__exact=todo",
                    "link": reverse_lazy("admin:pm_job_changelist"),
                },
            ],
        },
    ],
    "COMMAND": {
        "search_models": [
            "core.User",
            "pm.Job",
            "prj.Project",
            "pm.Session",
        ],
    },
    "SITE_DROPDOWN": [
        {
            "icon": "target",
            "title": "مشاهده سایت",
            "link": "/",
            "attrs": {"target": "_blank"},
        },
    ],
    "SITE_ICON": {
        "light": lambda request: static("logo.png"),
        "dark": lambda request: static("logo-white.png"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("logo.png"),
        "dark": lambda request: static("logo-white.png"),
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("logo.png"),
        },
    ],
    "LOGIN": {
        "image": lambda request: static("login-bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
        "form": "unfold.forms.AuthenticationForm",
    },

}
