from django import template
from prj.models import Project

register = template.Library()


def get_field_answer(field, flow, order=0):
    answer = field.answers.filter(flow=flow, order=order).first()
    if answer is None:
        return ''
    if field.type == 'projects':
        project = Project.objects.filter(id=answer.body).first()
        return project.title if project else ''
    if field.type == 'file':
        return 'فایل الصاق شده' if answer.body else ''
    if field.type == 'number' and answer.body.isnumeric():
        return f'{int(answer.body):,}:,'
    return answer.body


@register.filter()
def node_fields(node):
    data = []
    flow = node.flow
    fields = node.node_pattern.fields.all() if node.done_time else node.node_pattern.fields.filter(editable=False)
    for nodefield in fields:
        if nodefield.field.table:
            if nodefield.field.table not in map(lambda a: a['label'], data):
                head = []
                for f in node.node_pattern.fields.filter(field__table=nodefield.field.table):
                    head.append({
                        'id': f.field.id,
                        'label': f.field.label,
                        'type': f.field.type,
                        'answer': '',
                        'file': None,
                        'editable': f.editable
                    })
                rows = []
                for i in range(nodefield.field.answers.filter(flow=flow).count()):
                    row = []
                    for f in node.node_pattern.fields.filter(field__table=nodefield.field.table):
                        row.append({
                            'id': f.field.id,
                            'label': f.field.label,
                            'type': f.field.type,
                            'answer': get_field_answer(field=f.field, flow=flow, order=i),
                            'editable': f.editable
                        })
                    rows.append(row)
                data.append({
                    'id': 0,
                    'label': nodefield.field.table,
                    'type': 'table',
                    'row_min': nodefield.field.row_min,
                    'row_max': nodefield.field.row_max,
                    'head': head,
                    'rows': rows,
                })
        else:
            data.append({
                'id': nodefield.field.id,
                'label': nodefield.field.label,
                'type': nodefield.field.type,
                'table': nodefield.field.table,
                'answer': get_field_answer(field=nodefield.field, flow=flow),
                'editable': nodefield.editable
            })
    result = list(filter(lambda fi: fi['type'] == 'table' or fi['answer'], data))
    return result
