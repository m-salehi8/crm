from pm.models import Flow


def lottery():
    for f in Flow.objects.filter(flow_pattern_id=1).order_by('id'):
        print(f.user.id)
