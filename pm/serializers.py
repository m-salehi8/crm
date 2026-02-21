import jdatetime
from .models import *
from core.models import User
from rest_framework import serializers
from core.serializers import SerUserList
from django_jalali.serializers.serializerfield import JDateField


class SerMembers(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='get_full_name')
    unit = serializers.IntegerField(read_only=True, source='post.unit.id')

    class Meta:
        model = User
        fields = ['id', 'name', 'photo_url', 'unit']


class SerTag(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = 'id', 'user', 'title', 'order'


class SerTaskListInJob(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    photo_url = serializers.CharField(read_only=True, source='user.photo_url')

    class Meta:
        model = Task
        fields = ['user', 'name', 'photo_url', 'is_owner', 'is_committed']


class SerJob(serializers.ModelSerializer):
    deadline = JDateField(allow_null=True)
    has_note = serializers.SerializerMethodField()
    has_appendix = serializers.SerializerMethodField()
    tasks = SerTaskListInJob(read_only=True, many=True)
    is_manager = serializers.SerializerMethodField()


    def get_is_manager(self, obj):
        try:
            user = self.context.get('user')
            return user.post.is_manager
        except:
            return False


    def get_has_note(self, obj):
        return obj.note is not None and len(obj.note) > 0

    def get_has_appendix(self, obj):
        return obj.appendices.exists()

    class Meta:
        model = Job
        fields = ['is_manager', 'id', 'project', 'approval', 'session', 'deadline', 'status', 'done_time', 'confirm', 'suspended', 'title', 'urgency', 'archive', 'has_note', 'note', 'has_appendix', 'respite', 'has_chat', 'tasks']


class SerTaskList(serializers.ModelSerializer):
    job = SerJob(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'user', 'is_owner', 'is_seen', 'tag', 'order', 'unseen_chat_count', 'job']


class SerTaskListV2(serializers.ModelSerializer):
    job = SerJob(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'user', 'is_seen', 'tag', 'order', 'unseen_chat_count', 'job']


class SerJobChat(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    photo_url = serializers.CharField(read_only=True, source='user.photo_url')
    send_time = serializers.SerializerMethodField()

    def get_send_time(self, obj):
        return str(obj.send_time)[:19]

    class Meta:
        model = JobChat
        fields = ['id', 'user', 'name', 'photo_url', 'body', 'file', 'file_url', 'send_time']


class SerJobAppendix(serializers.ModelSerializer):
    class Meta:
        model = JobAppendix
        fields = ['id', 'job', 'title', 'file_url', 'file']


class SerJobDetail(serializers.ModelSerializer):
    project_title = serializers.CharField(read_only=True, source='project.title')
    session_title = serializers.CharField(read_only=True, source='session.title')
    session_date = serializers.CharField(read_only=True, source='session.date')
    approval_session_title = serializers.CharField(read_only=True, source='approval.session.title')
    approval_session_date = serializers.CharField(read_only=True, source='approval.session.date')
    deadline = JDateField(allow_null=True)
    tasks = SerTaskListInJob(read_only=True, many=True)
    appendices = SerJobAppendix(read_only=True, many=True)
    chats = SerJobChat(read_only=True, many=True)
    informees = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'project', 'project_title', 'title', 'approval', 'session', 'session_title', 'session_date', 'approval_session_title', 'approval_session_date', 'note', 'deadline', 'respite', 'status', 'suspended', 'urgency', 'archive', 'create_time', 'tasks', 'appendices', 'chats', 'informees']

    def get_informees(self, obj):
        try:
            data = []
            for us in obj.informees.all():
                data.append({
                    'id': us.id,
                    'name': us.name,
                    'photo_url': us.photo_url,
                })
            return data
        except Exception as e:
            return str(e)

class SerTaskDetail(serializers.ModelSerializer):
    job = SerJobDetail(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'user', 'is_owner', 'tag', 'order', 'job', ]


# صورتجلسات


class SerSessionList(serializers.ModelSerializer):
    color = serializers.CharField(read_only=True, source='room.color')
    room = serializers.CharField(read_only=True, source='room.title')
    public = serializers.BooleanField(read_only=True, source='room.public')
    department = serializers.CharField(read_only=True, source='user.post.unit.department.title')

    class Meta:
        model = Session
        fields = ['id', 'user', 'unit', 'title', 'date', 'register_time', 'time', 'room', 'approval_count', 'color', 'accept_room', 'public', 'department', 'need_breakfast', 'need_lunch', 'need_catering', 'request_time', 'order_time', 'need_manager', 'need_deputy', 'manager_accept', 'deputy_accept']


class SerApprovalEditList(serializers.ModelSerializer):
    deadline = JDateField(allow_null=True)
    member_list = serializers.SerializerMethodField()

    def get_member_list(self, session):
        return [m.get_full_name() for m in session.members.all()]

    class Meta:
        model = Approval
        fields = ['id', 'title', 'is_done', 'deadline', 'members', 'member_list']


class SerVisitant(serializers.ModelSerializer):
    class Meta:
        model = Visitant
        fields = ['id', 'session', 'name', 'nf', 'nf_accept']


class SerApproval(serializers.ModelSerializer):
    session = serializers.CharField(read_only=True, source='session.title')
    date = serializers.CharField(read_only=True, source='session.date')
    members = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    respite = serializers.SerializerMethodField()

    def get_members(self, approval):
        return [{'id': t.id, 'name': t.user.get_full_name(), 'photo_url': t.user.photo_url} for t in Task.objects.filter(job__approval=approval, is_committed=True)]

    def get_can_edit(self, approval):
        return approval.session.user == self.context['user']

    def get_respite(self, approval):
        return (approval.deadline - jdatetime.datetime.now().date()).days if approval.deadline else None

    class Meta:
        model = Approval
        fields = ['id', 'title', 'is_done', 'deadline', 'session', 'date', 'respite', 'can_edit', 'members']


class SerSessionDetail(serializers.ModelSerializer):
    date = JDateField()
    room_title = serializers.CharField(read_only=True, source='room.title')
    color = serializers.CharField(read_only=True, source='room.color')
    approvals = SerApprovalEditList(many=True)
    approvals_list = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    member_list = serializers.SerializerMethodField()
    today = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    secretaries = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()

    def get_approvals_list(self, obj):
        data = Approval.objects.filter(session=obj)
        user = self.context['user']
        ser_data = SerApprovalEditList(data, many=True, context={'user': user}).data
        return ser_data

    def get_rate(self, session):
        rates = SessionRate.objects.filter(session=session)
        if rates.exists():
            rate = 0
            count = 0
            for i, r in enumerate(rates):
                rate += r.rate
                count += 1

            rate = rate / count
            return int(rate) #round(rate, 2)
        return 0


    def get_secretaries(self, session):
        return [m.get_full_name() for m in session.secretaries.all()]

    def get_member_list(self, session):
        return [m.get_full_name() for m in session.members.all()]

    def get_can_edit(self, session):
        access = session.user == self.context['user'] or self.context['user'] in session.secretaries.all()
        return access

    def get_today(self, session):
        return str(jdatetime.datetime.now().date())

    def get_start(self, session):
        return str(session.start)[:-3] if session.start else None

    def get_end(self, session):
        return str(session.end)[:-3] if session.end else None

    class Meta:
        model = Session
        fields = ['secretaries','approvals_list','id', 'type', 'title', 'date', 'weekday', 'start', 'end', 'place', 'room', 'room_title', 'color', 'sms', 'need_breakfast', 'need_lunch', 'need_catering', 'order_time', 'breakfast', 'lunch', 'catering', 'need_manager', 'need_deputy', 'manager_accept', 'deputy_accept', 'manager_note', 'deputy_note',
                  'breakfast_agents', 'lunch_agents', 'catering_agents', 'can_edit', 'today', 'need_photography', 'need_filming', 'need_recording', 'need_news', 'need_presentation', 'accept_room', 'accept_photography', 'accept_filming', 'accept_recording', 'accept_news', 'accept_presentation', 'cancel_time', 'approvals', 'members', 'member_list', 'agenda', 'guest_count', 'project', 'rate']


class SerRoom(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'title', 'public', 'location', 'capacity', 'facilities']

# Flow:


class SerField(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['id', 'label', 'hint', 'type', 'choices', 'table', 'row_min', 'row_max', 'order', 'is_archived']


class SerNode(serializers.ModelSerializer):
    flow_title = serializers.CharField(read_only=True, source='flow.flow_pattern.title')
    image = serializers.CharField(read_only=True, source='flow.flow_pattern.image.name')
    form_width = serializers.CharField(read_only=True, source='flow.flow_pattern.form_width')
    quota_per_user = serializers.CharField(read_only=True, source='flow.flow_pattern.quota_per_user')
    flow_user_name = serializers.CharField(read_only=True, source='flow.user.get_full_name')
    flow_user_photo = serializers.CharField(read_only=True, source='flow.user.photo_url')
    flow_user_post = serializers.CharField(read_only=True, source='flow.user.post.title')
    flow_user_unit = serializers.CharField(read_only=True, source='flow.user.post.unit.title')
    flow_user_personnel_code = serializers.IntegerField(read_only=True, source='flow.user.personnel_code')
    node_title = serializers.CharField(read_only=True, source='node_pattern.title')
    node_next = serializers.IntegerField(read_only=True, source='node_pattern.next.id')

    class Meta:
        model = Node
        fields = ['id', 'flow_title', 'image', 'form_width', 'quota_per_user', 'flow', 'flow_user_name', 'flow_user_photo', 'flow_user_post', 'node_next',
                  'flow_user_unit', 'flow_user_personnel_code', 'node_pattern', 'node_title', 'create_time', 'seen_time', 'done_time', 'removable', 'revertable']


class SerFlowHistory(serializers.ModelSerializer):
    node_title = serializers.CharField(read_only=True, source='node_pattern.title')
    user_name = serializers.CharField(read_only=True, source='user.get_full_name')
    user_photo = serializers.CharField(read_only=True, source='user.photo_url')

    class Meta:
        model = Node
        fields = ['id', 'node_title', 'user_name', 'user_photo', 'create_time', 'seen_time', 'done_time']


class SerFlowPatternList(serializers.ModelSerializer):
    node_count = serializers.SerializerMethodField()
    flow_count = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_node_count(self, obj):
        return obj.nodes.count()

    def get_flow_count(self, obj):
        return obj.flows.count()

    def get_type(self, obj):
        return obj.flow_type.title if obj.flow_type else ''

    class Meta:
        model = FlowPattern
        fields = ['id', 'title', 'type', 'quota_per_user', 'active', 'node_count', 'flow_count', 'active']


class SerNodeField(serializers.ModelSerializer):
    class Meta:
        model = NodeField
        fields = ['id', 'field', 'editable', 'required']


class SerDispatchIf(serializers.ModelSerializer):
    class Meta:
        model = DispatchIf
        fields = ['id', 'type', 'key', 'value', 'values']


class SerDispatch(serializers.ModelSerializer):
    ifs = SerDispatchIf(read_only=True, many=True)

    class Meta:
        model = Dispatch
        fields = ['id', 'start', 'end', 'send_to_owner', 'send_to_parent', 'send_to_manager', 'send_to_posts', 'if_operator', 'ifs']


class SerNodePattern(serializers.ModelSerializer):
    fields = SerNodeField(read_only=True, many=True)
    dispatches = serializers.SerializerMethodField()

    def get_dispatches(self, obj):
        return SerDispatch(Dispatch.objects.filter(start=obj), many=True).data

    class Meta:
        model = NodePattern
        fields = ['id', 'title', 'is_first', 'is_archived', 'is_bottleneck', 'order', 'next', 'fields', 'dispatches', 'sms', 'respite']


class SerFlowPatternDetail(serializers.ModelSerializer):
    poster = serializers.CharField(read_only=True, source='poster.name')
    image = serializers.CharField(read_only=True, source='image.name')
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.flow_type.title if obj.flow_type else ''

    class Meta:
        model = FlowPattern
        fields = ['id', 'title', 'type', 'posts', 'form_width', 'quota_per_user', 'active', 'preamble', 'poster', 'image']


class SerPostList(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, post):
        return f'{post.title} ({post.active_user_name})'

    class Meta:
        model = Post
        fields = ['id', 'title']


class SerRoomRequest(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source='user.get_full_name')
    unit = serializers.CharField(read_only=True, source='user.post.unit.title')
    room = serializers.CharField(read_only=True, source='room.title')
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    def get_start(self, session):
        return str(session.start)[:-3] if session.start else None

    def get_end(self, session):
        return str(session.end)[:-3] if session.end else None

    class Meta:
        model = Session
        fields = ['id', 'user', 'unit', 'title', 'room', 'date', 'start', 'end', 'member_count', 'guest_count', 'need_photography', 'need_filming', 'need_recording', 'need_news', 'need_presentation', 'accept_room', 'accept_photography', 'accept_filming', 'accept_recording', 'accept_news', 'accept_presentation', 'room_agents', 'photography_agents', 'filming_agents', 'recording_agents', 'news_agents', 'presentation_agents']
