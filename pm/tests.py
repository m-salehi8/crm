
def get_node_list(request):
    node_list = request.user.nodes.order_by('-id')
    _type = request.GET.get('type', 'همه')
    if _type != 'همه':
        node_list = node_list.filter(done_time__isnull=_type == 'منتظر اقدام')
    flow = int(request.GET.get('flow', 0))
    if flow:
        node_list = node_list.filter(flow__flow_pattern_id=flow)
    q = request.GET.get('q', None)
    if q:
        q_list = q.split(' ')
        q_filter = reduce(operator.and_, (
        Q(flow__flow_pattern__title__contains=q_text) | Q(flow__user__personnel_code__contains=q_text) | Q(
            flow__user__first_name__contains=q_text) | Q(flow__user__last_name__contains=q_text) | Q(
            flow__user__post__unit__title__contains=q_text) | Q(flow__answers__body__contains=q_text) | Q(
            flow_id=q_text if q_text.isdigit() else 0) for q_text in q_list))
        node_list = node_list.filter(q_filter).distinct()
    return node_list


class NodeList(GenericAPIView):
    def get(self, request):
        node_list = get_node_list(request)
        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), node_list.count() // 10 + 1)
        data = {
            'type': request.GET.get('type', 'همه'),
            'q': request.GET.get('q', None),
            'count': node_list.count(),
            'page': page,
            'size': size,
            'flow': int(request.GET.get('flow', 0)),
            'list': SerNode(node_list[size * (page - 1):size * page], many=True).data
        }
        return Response(data=data)


class NodeListExcel(GenericAPIView):
    def get(self, request):
        node_list = get_node_list(request)
        wb = Workbook()
        ws = wb.active
        ws.title = f'flows-{str(jdatetime.date.today())}'
        ws.sheet_view.rightToLeft = True
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 35
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 35
        ws.column_dimensions['H'].width = 16
        ws.column_dimensions['I'].width = 16
        ws.append(['گزارش:', 'فهرست فرآیندها', '', 'توسط:', request.user.get_full_name(), '', '', 'زمان:',
                   jdatetime.datetime.now().strftime('%Y-%m-%d %H:%M')])
        ws.append(['', '', '', '', '', '', '', '', ''])
        ws.append(['شماره', 'وضعیت', 'فرآیند', 'گره', 'متقاضی', 'کد پرسنلی', 'واحد', 'زمان دریافت', 'زمان ارسال'])
        for node in node_list:
            ws.append([node.flow_id,
                       'مشاهده نشده' if node.seen_time is None else 'منتظر اقدام' if node.done_time is None else 'اقدام شده',
                       node.flow.flow_pattern.title, node.node_pattern.title, node.flow.user.get_full_name(),
                       node.flow.user.personnel_code, node.flow.user.post.unit.title if node.flow.user.post else '',
                       node.create_time.strftime('%Y-%m-%d %H:%M'),
                       node.done_time.strftime('%Y-%m-%d %H:%M') if node.done_time else ''])
        table = Table(displayName="FlowTable", ref=f'A3:I{ws.max_row}')
        table.tableStyleInfo = TableStyleInfo(name='TableStyleMedium9', showRowStripes=True)
        ws.add_table(table)
        farsi_style = styles.NamedStyle(name='farsi_style')
        farsi_style.font = styles.Font(name='Sahel', size=10)
        wb.add_named_style(farsi_style)
        for row in ws.iter_rows():
            for cell in row:
                cell.style = 'farsi_style'
        grey_style = styles.NamedStyle(name='grey_style')
        grey_style.font = styles.Font(name='Sahel', size=10, color='FF808080')
        grey_style.alignment = styles.Alignment(horizontal='left', vertical='center')
        for i in ['A1', 'D1', 'H1']:
            cell = ws[i]
            cell.style = grey_style
        bold_style = styles.NamedStyle(name='bold_style')
        bold_style.font = styles.Font(name='Sahel', size=10, bold=True)
        bold_style.fill = styles.PatternFill(start_color="FFFFE4E1", end_color="FFFFE4E1", fill_type="solid")
        for i in ['B1', 'E1', 'I1']:
            cell = ws[i]
            cell.style = bold_style
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        response = HttpResponse(content=output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=flows-{str(jdatetime.date.today())}.xlsx'
        return response


class MyFlowPatterList(GenericAPIView):
    def get(self, request):
        data = [{'id': fp.id, 'title': fp.title, 'type': fp.flow_type.title if fp.flow_type else ''} for fp in
                FlowPattern.objects.filter(posts__in=[request.user.post], active=True).order_by('title') if
                fp.quota_per_user > request.user.flows.filter(flow_pattern=fp).count()]
        return Response(data=data)


class AllFlowPatterList(GenericAPIView):
    def get(self, request):
        data = [{'id': fp.id, 'title': fp.title} for fp in
                FlowPattern.objects.filter(active=True, nodes__nodes__user=request.user).distinct()]
        return Response(data=data)


def get_field_answer(field, flow, order=0):
    answer = field.answers.filter(flow=flow, order=order).first()
    return answer.body if answer and answer.body else None


def get_field_file(field, flow, order=0):
    answer = field.answers.filter(flow=flow, order=order).first()
    return str(answer.file) if answer and answer.file else None


class NodeDetail(GenericAPIView):
    def get(self, request, pk):
        node = get_object_or_404(Node, pk=pk, user=request.user)
        if node.seen_time is None:
            node.seen_time = jdatetime.datetime.now()
            node.save()
        request.user.notifications.filter(node=node).update(seen_time=jdatetime.datetime.now())
        flow = node.flow
        data = SerNode(node).data
        data['fields'] = []
        for nodefield in node.node_pattern.fields.all():
            if nodefield.field.table:
                if nodefield.field.table not in map(lambda a: a['label'], data['fields']):
                    head = []
                    for f in node.node_pattern.fields.filter(field__table=nodefield.field.table):
                        head.append({
                            'id': f.field.id,
                            'label': f.field.label,
                            'hint': f.field.hint,
                            'type': f.field.type,
                            'choices': f.field.choices,
                            'answer': '',
                            'file': None,
                            'new_file': None,
                            'editable': f.editable,
                            'required': f.required
                        })
                    rows = []
                    for i in range(nodefield.field.answers.filter(flow=flow).count()):
                        row = []
                        for f in node.node_pattern.fields.filter(field__table=nodefield.field.table):
                            row.append({
                                'id': f.field.id,
                                'label': f.field.label,
                                'hint': f.field.hint,
                                'type': f.field.type,
                                'choices': f.field.choices,
                                'answer': get_field_answer(field=f.field, flow=flow, order=i),
                                'file': get_field_file(field=f.field, flow=flow, order=i),
                                'new_file': None,
                                'editable': f.editable,
                                'required': f.required
                            })
                        rows.append(row)
                    data['fields'].append({
                        'id': 0,
                        'label': nodefield.field.table,
                        'type': 'table',
                        'row_min': nodefield.field.row_min,
                        'row_max': nodefield.field.row_max,
                        'head': head,
                        'rows': rows,
                    })
            else:
                data['fields'].append({
                    'id': nodefield.field.id,
                    'label': nodefield.field.label,
                    'hint': nodefield.field.hint,
                    'type': nodefield.field.type,
                    'choices': nodefield.field.choices,
                    'table': nodefield.field.table,
                    'answer': get_field_answer(field=nodefield.field, flow=flow),
                    'file': get_field_file(field=nodefield.field, flow=flow),
                    'new_file': None,
                    'editable': nodefield.editable,
                    'required': nodefield.required
                })
        return Response(data=data)


class GetNodePdf(GenericAPIView):
    def get(self, request, pk):
        node = get_object_or_404(Node, pk=pk, user=request.user)
        html_string = render_to_string('node.html', {'node': node})
        response = HttpResponse(HTML(string=html_string).write_pdf(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cover{node.flow_id}.pdf"'
        return response


def check_ifs(dispatch, node):
    if not dispatch.ifs.exists():
        return True
    if dispatch.if_operator == 'and':
        for item in dispatch.ifs.all():
            answer = get_field_answer(field=item.key, flow=node.flow, order=0)
            file = get_field_file(field=item.key, flow=node.flow, order=0)
            if (item.type == 'خالی' and ((item.key.type != 'file' and answer) or (item.key.type == 'file' and file))) \
                    or (item.type == 'دارای مقدار' and (
                    (item.key.type != 'file' and answer is None) or (item.key.type == 'file' and file is None))) \
                    or (item.type == 'مساوی' and answer != item.value) \
                    or (item.type == 'نامساوی' and answer == item.value) \
                    or (item.type == 'بزرگتر' and answer <= item.value) \
                    or (item.type == 'بزرگتر یا مساوی' and answer < item.value) \
                    or (item.type == 'کوچکتر' and answer >= item.value) \
                    or (item.type == 'کوچکتر یا مساوی' and answer > item.value):
                return False
            # وقتی نوع فیلد «چندانتخابی» است آرایه گزینه‌های فیلد و آرایه گزینه‌های شرط اگر اشتراک داشت جواب مثبت است
            if item.type == 'موجود در لیست':
                if item.key.type == 'multi-select':
                    if not bool(set(answer.split(',')) & set(item.values)):
                        return False
                elif answer not in item.values:
                    return False
            if item.type == 'ناموجود در لیست':
                if item.key.type == 'multi-select':
                    if bool(set(answer.split(',')) & set(item.values)):
                        return False
                elif answer in item.values:
                    return False
        return True
    else:
        for item in dispatch.ifs.all():
            answer = get_field_answer(field=item.key, flow=node.flow, order=0)
            file = get_field_file(field=item.key, flow=node.flow, order=0)
            if (item.type == 'خالی' and (
                    (item.key.type != 'file' and answer is None) or (item.key.type == 'file' and file is None))) \
                    or (item.type == 'دارای مقدار' and (
                    (item.key.type != 'file' and answer) or (item.key.type == 'file' and file))) \
                    or (item.type == 'مساوی' and answer == item.value) \
                    or (item.type == 'نامساوی' and answer != item.value) \
                    or (item.type == 'بزرگتر' and answer > item.value) \
                    or (item.type == 'بزرگتر یا مساوی' and answer >= item.value) \
                    or (item.type == 'کوچکتر' and answer < item.value) \
                    or (item.type == 'کوچکتر یا مساوی' and answer <= item.value):
                return True
            # وقتی نوع فیلد «چندانتخابی» است آرایه گزینه‌های فیلد و آرایه گزینه‌های شرط اگر اشتراک داشت جواب مثبت است
            if item.type == 'موجود در لیست':
                if item.key.type == 'multi-select':
                    if bool(set(answer.split(',')) & set(item.values)):
                        return True
                elif answer in item.values:
                    return True
            if item.type == 'ناموجود در لیست':
                if item.key.type == 'multi-select':
                    if not bool(set(answer.split(',')) & set(item.values)):
                        return True
                elif answer not in item.values:
                    return True
        return False


class NodeSave(GenericAPIView):
    def post(self, request):
        if request.data['node'] == '0':
            node_pattern = get_object_or_404(NodePattern, pk=request.data['node_pattern'])
            if node_pattern.flow_pattern.quota_per_user <= request.user.flows.filter(
                    flow_pattern=node_pattern.flow_pattern).count():
                return Response(data='سقف تعداد فرآیند تکمیل شده است', status=status.HTTP_400_BAD_REQUEST)
            flow = Flow.objects.create(user=request.user, flow_pattern_id=node_pattern.flow_pattern_id)
            node = Node.objects.create(flow=flow, user=request.user, post=request.user.post, node_pattern=node_pattern,
                                       seen_time=jdatetime.datetime.now())
            field = Field.objects.filter(flow_pattern=node_pattern.flow_pattern, label='level').first()
            if field:
                Answer.objects.create(flow=flow, field=field, body=request.user.post.level)
            field = Field.objects.filter(flow_pattern=node_pattern.flow_pattern, label='unit').first()
            if field:
                Answer.objects.create(flow=flow, field=field, body=request.user.post.unit.title)
        else:
            node = get_object_or_404(Node, pk=request.data['node'], user=request.user)
        for data in request.data.getlist('removing_rows', []):
            table_name = data[:data.rfind('-')]
            row_index = int(data[data.rfind('-') + 1:])
            Answer.objects.filter(flow=node.flow, field__table=table_name, order=row_index).delete()
        for data in request.data.getlist('removing_files', []):
            field_id = int(data[:data.find('-')])
            row_index = int(data[data.find('-') + 1:])
            Answer.objects.filter(flow=node.flow, field_id=field_id, order=row_index).delete()
        for data in request.data:
            if data[:6] == 'answer':
                tmp = data[7:]
                field_id = int(tmp[:tmp.find('-')])
                row_index = int(tmp[tmp.find('-') + 1:])
                answer, created = Answer.objects.get_or_create(flow=node.flow, field_id=field_id, order=row_index)
                answer.body = request.data[data]
                answer.save()
            elif data[:4] == 'file':
                tmp = data[5:]
                field_id = int(tmp[:tmp.find('-')])
                row_index = int(tmp[tmp.find('-') + 1:])
                answer, created = Answer.objects.get_or_create(flow=node.flow, field_id=field_id, order=row_index)
                answer.file = request.data[data]
                answer.save()
        node.done_time = jdatetime.datetime.now()
        node.save()
        owner = node.flow.nodes.order_by('pk')[0].user
        for dispatch in Dispatch.objects.filter(start=node.node_pattern):
            if check_ifs(dispatch=dispatch, node=node):
                if dispatch.send_to_owner:
                    new_node = Node.objects.create(flow=node.flow, user=node.flow.user, post=node.flow.user.post,
                                                   node_pattern=dispatch.end)
                    Notification.objects.create(user_id=node.flow.user_id, title=node.flow.flow_pattern.title,
                                                body=node.node_pattern.title, url=f'/flow?id={new_node.id}',
                                                node=new_node)
                if dispatch.send_to_parent:
                    parent = owner.post.parent.active_user or owner.post.unit.manager or owner.post.unit.parent.manager
                    new_node = Node.objects.create(flow=node.flow, user=parent, post=parent.post,
                                                   node_pattern=dispatch.end)
                    Notification.objects.create(user=parent, title=node.flow.flow_pattern.title,
                                                body=node.node_pattern.title, url=f'/flow?id={new_node.id}',
                                                node=new_node)
                    # اگر کاربر موردنظر یافت نشود به مدیر مجموعه ارجاع می‌شود
                if dispatch.send_to_manager:
                    new_node = Node.objects.create(flow=node.flow, user=owner.post.unit.manager,
                                                   post=owner.post.unit.manager.post if owner.post.unit.manager else None,
                                                   node_pattern=dispatch.end)
                    Notification.objects.create(user=owner.post.unit.manager, title=node.flow.flow_pattern.title,
                                                body=node.node_pattern.title, url=f'/flow?id={new_node.id}',
                                                node=new_node)
                for post in dispatch.send_to_posts.all():
                    user = post.active_user or post.parent.active_user
                    if user:
                        new_node = Node.objects.create(flow=node.flow, user=user, post=user.post,
                                                       node_pattern=dispatch.end)
                        Notification.objects.create(user=user, title=node.flow.flow_pattern.title,
                                                    body=node.node_pattern.title, url=f'/flow?id={new_node.id}',
                                                    node=new_node)
        if node.node_pattern.next:
            for user_id in request.data.getlist('next_users', []):
                user = User.objects.get(id=user_id)
                new_node = Node.objects.create(flow=node.flow, user=user, post=user.post,
                                               node_pattern=node.node_pattern.next)
                Notification.objects.create(user=user, title=node.flow.flow_pattern.title, body=node.node_pattern.title,
                                            url=f'/flow?id={new_node.id}', node=new_node)
        data = {
            'todo_flow': request.user.todo_flow,
            'node': SerNode(node).data,
        }
        return Response(data=data)


class NodeRemove(GenericAPIView):
    def post(self, request):
        node = get_object_or_404(Node, pk=request.data['pk'], user=request.user)
        if node.removable:
            node.flow.delete()
            return Response(data=request.user.todo_task)
        return Response(data='denied', status=status.HTTP_403_FORBIDDEN)


class NodeRevert(GenericAPIView):
    def post(self, request):
        node = get_object_or_404(Node, pk=request.data['pk'], user=request.user, done_time__isnull=False)
        ends = Dispatch.objects.filter(start=node.node_pattern).values_list('end', flat=True)
        if Node.objects.filter(node_pattern_id__in=ends, flow=node.flow, create_time__gte=node.done_time,
                               create_time__lt=(node.done_time + jdatetime.timedelta(seconds=1)),
                               seen_time__isnull=False).exists():
            return Response(data='گره بعدی توسط یکی از کاربران مشاهده شد', status=status.HTTP_403_FORBIDDEN)
        Node.objects.filter(node_pattern_id__in=ends, flow=node.flow, create_time__gte=node.done_time,
                            create_time__lt=(node.done_time + jdatetime.timedelta(seconds=1))).delete()
        node.done_time = None
        node.save()
        fields = NodeField.objects.filter(node=node.node_pattern, editable=True).values_list('field', flat=True)
        Answer.objects.filter(flow=node.flow, field_id__in=fields).delete()
        data = {
            'todo_flow': request.user.todo_flow,
            'node': SerNode(node).data,
        }
        return Response(data=data)


class StartNewFlow(GenericAPIView):
    def get(self, request, pk):
        node_pattern = NodePattern.objects.filter(flow_pattern_id=pk, flow_pattern__posts__in=[request.user.post],
                                                  is_first=True).first()
        data = {'id': 0,
                'form_width': node_pattern.flow_pattern.form_width,
                'quota_per_user': node_pattern.flow_pattern.quota_per_user,
                'flow_title': node_pattern.flow_pattern.title,
                'flow_user_name': request.user.get_full_name(),
                'flow_user_photo': request.user.photo_url,
                'flow_user_department': request.user.post.unit.department.title,
                'flow_user_personnel_code': request.user.personnel_code,
                'node_pattern': node_pattern.id,
                'node_title': node_pattern.title,
                'node_next': node_pattern.next_id,
                'create_time': str(jdatetime.datetime.now()),
                'done_time': None,
                'preamble': node_pattern.flow_pattern.preamble,
                'poster': node_pattern.flow_pattern.poster.name if node_pattern.flow_pattern.poster else None,
                'image': node_pattern.flow_pattern.image.name if node_pattern.flow_pattern.image else None,
                'fields': []
                }
        for nodefield in node_pattern.fields.all():
            if nodefield.field.table:
                if nodefield.field.table not in map(lambda a: a['label'], data['fields']):
                    head = []
                    for f in node_pattern.fields.filter(field__table=nodefield.field.table):
                        head.append({
                            'id': f.field.id,
                            'label': f.field.label,
                            'hint': f.field.hint,
                            'type': f.field.type,
                            'choices': f.field.choices,
                            'answer': [] if f.field.type == 'multi-select' else '',
                            'file': None,
                            'new_file': None,
                            'editable': f.editable,
                            'required': f.required
                        })
                    data['fields'].append({
                        'id': 0,
                        'label': nodefield.field.table,
                        'type': 'table',
                        'row_min': nodefield.field.row_min,
                        'row_max': nodefield.field.row_max,
                        'head': head,
                        'rows': []
                    })
            else:
                data['fields'].append({
                    'id': nodefield.field.id,
                    'label': nodefield.field.label,
                    'hint': nodefield.field.hint,
                    'type': nodefield.field.type,
                    'choices': nodefield.field.choices,
                    'table': nodefield.field.table,
                    'answer': [] if nodefield.field.type == 'multi-select' else '',
                    'file': None,
                    'new_file': None,
                    'editable': nodefield.editable,
                    'required': nodefield.required
                })
        return Response(data=data)


class FlowHistory(GenericAPIView):
    def get(self, request, pk):
        node = get_object_or_404(Node, pk=pk, user=request.user)
        return Response(data=SerFlowHistory(node.flow.nodes, many=True).data)


class FlowPatternAdd(CreateAPIView):
    permission_classes = [IsFlowAdmin]
    queryset = FlowPattern.objects.all()
    serializer_class = SerFlowPatternDetail


class FlowPatternRemove(DestroyAPIView):
    permission_classes = [IsFlowAdmin]
    queryset = FlowPattern.objects.all()


class FlowPatternList(GenericAPIView):
    permission_classes = [IsFlowAdmin]

    def get(self, request):
        _type = request.GET.get('type', 'همه')
        if _type == 'همه':
            flow_pattern_list = FlowPattern.objects.all()
        else:
            flow_pattern_list = FlowPattern.objects.filter(flow_type__title=_type)
        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), flow_pattern_list.count() // 10 + 1)
        data = {
            'count': flow_pattern_list.count(),
            'page': page,
            'size': size,
            'type': _type,
            'list': SerFlowPatternList(instance=flow_pattern_list[size * (page - 1):size * page], many=True).data
        }
        return Response(data=data)


class FlowPatternDetail(RetrieveAPIView):
    permission_classes = [IsFlowAdmin]
    queryset = FlowPattern.objects.all()
    serializer_class = SerFlowPatternDetail


class FlowPatternFields(ListAPIView):
    permission_classes = [IsFlowAdmin]
    serializer_class = SerField

    def get_queryset(self):
        flow_pattern = get_object_or_404(FlowPattern, pk=self.kwargs['pk'])
        return flow_pattern.fields


class FlowPatternNodes(ListAPIView):
    permission_classes = [IsFlowAdmin]
    serializer_class = SerNodePattern

    def get_queryset(self):
        flow_pattern = get_object_or_404(FlowPattern, pk=self.kwargs['pk'])
        return flow_pattern.nodes


class SaveFlowPatternDetail(GenericAPIView):
    permission_classes = [IsFlowAdmin]

    def post(self, request):
        if request.data['id']:
            fp = get_object_or_404(FlowPattern, pk=request.data['id'])
            fp.title = request.data['title']
            # Set the flow_type based on the type value
            flow_type_obj, created = FlowPatternType.objects.get_or_create(title=request.data['type'])
            fp.flow_type = flow_type_obj
            fp.form_width = request.data['form_width']
            fp.quota_per_user = request.data['quota_per_user']
            fp.active = request.data['active'] == 'true'
            fp.preamble = request.data['preamble']
            fp.save()
        else:
            # Create or get the flow_type object
            flow_type_obj, created = FlowPatternType.objects.get_or_create(title=request.data['type'])
            fp = FlowPattern.objects.create(title=request.data['title'], flow_type=flow_type_obj,
                                            form_width=request.data['form_width'],
                                            quota_per_user=request.data['quota_per_user'],
                                            active=request.data['active'], preamble=request.data['preamble'])
        if 'new_poster' in request.data:
            fp.poster = request.data['new_poster']
        elif request.data['poster'] == 'removed':
            fp.poster = None
        if 'new_image' in request.data:
            fp.image = request.data['new_image']
        elif request.data['image'] == 'removed':
            fp.image = None
        fp.save()
        fp.posts.set(request.data.getlist('posts'))
        return Response(data=SerFlowPatternDetail(fp).data)


class SaveFlowPatternFields(GenericAPIView):
    permission_classes = [IsFlowAdmin]

    def post(self, request):
        flow_pattern = get_object_or_404(FlowPattern, id=request.data['id'])
        ids = list(map(lambda f: f['id'], request.data['fields']))
        flow_pattern.fields.exclude(id__in=ids).delete()
        for data_index, data in enumerate(request.data['fields']):
            if data['id'] == 0:
                flow_pattern.fields.create(label=data['label'], hint=data['hint'], type=data['type'],
                                           choices=data['choices'], table=data['table'], row_min=data['row_min'],
                                           row_max=data['row_max'], order=data_index, is_archived=data['is_archived'])
            else:
                flow_pattern.fields.filter(id=data['id']).update(label=data['label'], hint=data['hint'],
                                                                 type=data['type'], choices=data['choices'],
                                                                 table=data['table'], row_min=data['row_min'],
                                                                 row_max=data['row_max'], order=data_index,
                                                                 is_archived=data['is_archived'])
        return Response(data=SerField(flow_pattern.fields, many=True).data)


class SaveFlowPatternNodes(GenericAPIView):
    permission_classes = [IsFlowAdmin]

    def post(self, request):
        flow_pattern = get_object_or_404(FlowPattern, id=request.data['id'])
        # remove unlisted nodes:
        ids = list(map(lambda f: f['id'], request.data['nodes']))
        flow_pattern.nodes.exclude(id__in=ids).delete()
        # create or update nodes:
        for data_index, data in enumerate(request.data['nodes']):
            if data['id'] == 0:
                node = flow_pattern.nodes.create(title=data['title'], order=data_index, next_id=data['next'],
                                                 is_archived=data['is_archived'], is_bottleneck=data['is_bottleneck'],
                                                 respite=data['respite'])
            else:
                node = flow_pattern.nodes.get(id=data['id'])
                node.title = data['title']
                node.order = data_index
                node.next_id = data['next']
                node.is_archived = data['is_archived']
                node.is_bottleneck = data['is_bottleneck']
                node.is_first = data['is_first']
                node.sms = data['sms']
                node.respite = data['respite']
                node.save()
            # remove unlisted node_fields:
            ids = list(map(lambda f: f['field'], data['fields']))
            node.fields.exclude(field_id__in=ids).delete()
            # create or update node_fields:
            for field_data in data['fields']:
                node_field, created = node.fields.get_or_create(field_id=field_data['field'])
                node_field.editable = field_data['editable']
                node_field.required = field_data['required']
                node_field.save()
            # remove unlisted dispatches:
            ids = list(map(lambda f: f['id'], data['dispatches']))
            Dispatch.objects.filter(start=node).exclude(id__in=ids).delete()
            # create or update dispatches:
            for dispatch_date in data['dispatches']:
                if dispatch_date['id'] == 0:
                    dispatch = Dispatch.objects.create(start=node, end_id=dispatch_date['end'])
                else:
                    dispatch = Dispatch.objects.get(id=dispatch_date['id'])
                dispatch.end_id = dispatch_date['end']
                dispatch.send_to_owner = dispatch_date['send_to_owner']
                dispatch.send_to_parent = dispatch_date['send_to_parent']
                dispatch.send_to_manager = dispatch_date['send_to_manager']
                dispatch.send_to_posts.set(dispatch_date['send_to_posts'])
                dispatch.if_operator = dispatch_date['if_operator']
                dispatch.save()
                ids = list(map(lambda f: f['id'], dispatch_date['ifs']))
                dispatch.ifs.exclude(id__in=ids).delete()
                for dispatch_if_data in dispatch_date['ifs']:
                    if dispatch_if_data['id'] == 0:
                        dispatch_if = DispatchIf.objects.create(dispatch=dispatch, key_id=dispatch_if_data['key'],
                                                                type=dispatch_if_data['type'])
                    else:
                        dispatch_if = DispatchIf.objects.get(pk=dispatch_if_data['id'])
                        dispatch_if.key_id = dispatch_if_data['key']
                        dispatch_if.type = dispatch_if_data['type']
                    dispatch_if.value = dispatch_if_data['value']
                    dispatch_if.values = dispatch_if_data['values']
                    dispatch_if.save()
        return Response(data=SerNodePattern(flow_pattern.nodes, many=True).data)


class PostListForFlowPatternManagement(ListAPIView):
    permission_classes = [IsFlowAdmin]
    serializer_class = SerPostList
    queryset = Post.objects.all()



class FlowCategoryAPI(APIView):
    def get(self, request):
        resp = []
        # Get all flow pattern types from the FlowPatternType model
        flow_type_objects = FlowPatternType.objects.all()
        for flow_type_obj in flow_type_objects:
            items = FlowPattern.objects.filter(posts__in=[request.user.post], flow_type=flow_type_obj, active=True)

            # Handle special case for financial resources
            if flow_type_obj.title == 'مالی و سرمایه‌های انسانی':
                financial_type_obj, created = FlowPatternType.objects.get_or_create(title='مالی و سرمایه انسانی')
                items = FlowPattern.objects.filter(posts__in=[request.user.post], flow_type__in=[flow_type_obj, financial_type_obj], active=True)

            data = []
            for item in items:
                data.append({
                    'id': item.pk,
                    'title': item.title,
                    'is_active': item.active,
                })
            resp.append({
                'name': flow_type_obj.title,
                'count': len(items),
                'items': data,
            })

        return Response( resp)