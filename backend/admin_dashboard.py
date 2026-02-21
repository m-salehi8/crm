from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
import json
import jdatetime

from unfold.components import BaseComponent, register_component
from core.models import User, UserActivityLog
from pm.models import Job, Session, Flow
from prj.models import Project

def dashboard_callback(request, context):
    """
    Callback to provide data to the dashboard template.
    """
    # KPI Data
    context.update({
        "kpi_users": User.objects.filter(is_active=True).count(),
        "kpi_projects": Project.objects.count(),
        "kpi_jobs_pending": Job.objects.filter(status='todo').count(),
        "kpi_sessions_today": Session.objects.filter(date=jdatetime.date.today()).count(),
    })
    
    return context

@register_component
class FlowTypeChart(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group flows by pattern title
        flows = Flow.objects.values('flow_pattern__title').annotate(count=Count('id')).order_by('-count')
        
        labels = [f['flow_pattern__title'] for f in flows]
        data = [f['count'] for f in flows]
        
        context.update({
            "height": 300,
            "data": json.dumps({
                "labels": labels,
                "datasets": [
                    {
                        "label": str(_("تعداد فرآیندها")),
                        "data": data,
                        "backgroundColor": "var(--color-primary-500)",
                    }
                ]
            })
        })
        return context

@register_component
class ActivityChart(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get last 30 days activity
        last_30_days = timezone.now() - timedelta(days=30)
        activities = UserActivityLog.objects.filter(timestamp__gte=last_30_days)\
            .annotate(day=TruncDay('timestamp'))\
            .values('day')\
            .annotate(count=Count('id'))\
            .order_by('day')
            
        labels = [a['day'].strftime('%Y-%m-%d') for a in activities]
        data = [a['count'] for a in activities]
        
        context.update({
            "height": 300,
            "data": json.dumps({
                "labels": labels,
                "datasets": [
                    {
                        "label": str(_("فعالیت‌های اخیر")),
                        "data": data,
                        "borderColor": "var(--color-primary-500)",
                        "type": "line",
                        "fill": True,
                        "backgroundColor": "var(--color-primary-100)",
                    }
                ]
            })
        })
        return context
