import os
import django

# =========================
# تنظیمات Django
# =========================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


from django.db.models import Sum
from decimal import Decimal
from hr.models import Profile, Work, DeductionWork
from core.models import User

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from hr.models import Profile, Work, DeductionWork


def js_round(value):
    """معادل دقیق Math.round در JS"""
    return int(Decimal(value).quantize(0, rounding=ROUND_HALF_UP))




# -----------------------------------
# فرمت سه رقم سه رقم
# -----------------------------------
def format_number(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "0"


class SalaryCalculatorExact:

    def __init__(self, user, year, month):
        self.user = user
        self.year = year
        self.month = month

        self.profile = Profile.objects.get(user=user)
        self.work = Work.objects.get(user=user, year=year, month=month)

    # -----------------------------------
    # جمع کل آیتم‌های حکم (مثل فرانت)
    # -----------------------------------
    def get_sum(self):
        p = self.profile

        return (
            p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf8 + p.sf11 +
            p.sf14 + p.sf20 + p.sf27 + p.sf38 + p.sf42 +
            p.sf45 + p.sf49 + p.sf51 + p.sf52 + p.sf64 +
            p.sf65 + p.sf68 + p.sf69 + p.sf70 +
            p.sf_food + p.sf_house + p.sf_mobile + p.sf_commuting
        )

    # -----------------------------------
    # مبلغ اضافه‌کار
    # -----------------------------------
    def get_overtime_amount(self):
        p = self.profile
        w = self.work

        base_for_overtime = (
            p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf42 + p.sf45
        )

        divisor = 100 if p.is_advisor else 176

        overtime = w.overtime * base_for_overtime / divisor
        return js_round(overtime)

    # -----------------------------------
    # جمع مزایا ناخالص
    # -----------------------------------
    def get_gross_benefits(self):
        sum_salary = self.get_sum()
        overtime = self.get_overtime_amount()
        w = self.work
        p = self.profile

        gross = (
            (sum_salary * w.work_days / 30)
            + (w.bonus * 10)
            + overtime
            + p.sf_management
        )

        return js_round(gross)

    # -----------------------------------
    # مبلغ مشمول بیمه
    # -----------------------------------
    def get_insurance_covered(self):
        p = self.profile

        insurance_covered = (
            p.sf1 + p.sf5 + p.sf6 + p.sf7 + p.sf14 +
            p.sf20 + p.sf27 + p.sf38 + p.sf42 +
            p.sf45 + p.sf49 + p.sf51 + p.sf52 +
            p.sf64 + p.sf68 + p.sf69 + p.sf_house
        )

        return js_round(insurance_covered)

    # -----------------------------------
    # بیمه
    # -----------------------------------
    def get_insurance(self):
        p = self.profile

        if p.is_sacrificer or p.is_advisor or p.is_agent:
            return 0

        insurance = self.get_insurance_covered() * 0.07
        return js_round(insurance)

    # -----------------------------------
    # مالیات پلکانی دقیقاً مثل فرانت
    # -----------------------------------
    def get_tax(self):
        gross = self.get_gross_benefits()
        insurance = self.get_insurance()
        p = self.profile

        tax_covered = (
            gross
            - p.sf65
            - p.sf11
            - p.sf8
            - p.sf_food
            - p.sf_mobile
            - p.sf_commuting
            - (insurance * 2 / 7)
        )

        tax_covered = max(0, tax_covered)

        if p.is_sacrificer:
            return 0

        tax = (
            max(0, min(tax_covered, 300_000_000) - 240_000_000) * 0.1 +
            max(0, min(tax_covered, 380_000_000) - 300_000_000) * 0.15 +
            max(0, min(tax_covered, 500_000_000) - 380_000_000) * 0.2 +
            max(0, min(tax_covered, 666_666_667) - 500_000_000) * 0.25 +
            max(0, min(tax_covered, 999_999_999_999) - 666_666_667) * 0.3
        )

        return js_round(tax)

    # -----------------------------------
    # جمع کسورات
    # -----------------------------------
    def get_deductions(self):
        result = DeductionWork.objects.filter(
            user=self.user,
            year=self.year,
            month=self.month
        ).aggregate(total=Sum('value'))

        return result['total'] or 0

    # -----------------------------------
    # محاسبه نهایی (کاملاً مطابق فرانت)
    # -----------------------------------
    def calculate(self):

        sum_salary = self.get_sum()
        overtime = self.get_overtime_amount()
        gross = self.get_gross_benefits()
        insurance_covered = self.get_insurance_covered()
        insurance = self.get_insurance()
        tax = self.get_tax()
        deduction = self.get_deductions()

        net = (
            gross
            + (self.work.meed * 10)
            - insurance
            - tax
            - deduction
        ) / 10

        net = js_round(net)

        return {
            # مقادیر عددی
            "sum": js_round(sum_salary),
            "overtime": overtime,
            "gross_benefits": gross,
            "insurance_covered": insurance_covered,
            "insurance": insurance,
            "tax": tax,
            "deduction": deduction,
            "meed": self.work.meed * 10,
            "net_salary": net,

            # مقادیر نمایشی سه رقم سه رقم
            "sum_display": format_number(sum_salary),
            "overtime_display": format_number(overtime),
            "gross_benefits_display": format_number(gross),
            "insurance_covered_display": format_number(insurance_covered),
            "insurance_display": format_number(insurance),
            "tax_display": format_number(tax),
            "deduction_display": format_number(deduction),
            "meed_display": format_number(self.work.meed * 10),
            "net_salary_display": format_number(net),
        }

from django.db import transaction
from hr.models import Work

from hr.models import Work


def calculate_all_salaries(year=None, month=None):

    works = Work.objects.all()

    if year:
        works = works.filter(year=year)

    if month:
        works = works.filter(month=month)

    total = works.count()
    print(f"Found {total} work records")

    updated = 0
    errors = 0

    for work in works.select_related("user__profile"):

        try:
            salary = work.calculate_salary(save=True)
            print(f"✔ Work ID {work.id} → Salary: {salary:,}")
            updated += 1

        except Exception as e:
            print(f"✖ Error in Work ID {work.id} → {e}")
            errors += 1

    print("\n------ RESULT ------")
    print(f"Updated: {updated}")
    print(f"Errors: {errors}")


calculate_all_salaries()