import re
from .models import *
from fd.models import Reserve
from django.db.models import Q
from fn.models import InvoiceCover
from rest_framework import serializers


def validate_strong_password(value):
    """رمز باید بیشتر از ۸ کاراکتر و شامل عدد، حرف کوچک، حرف بزرگ و نماد باشد."""
    if len(value) < 8:
        raise serializers.ValidationError('رمز عبور باید حداقل ۸ کاراکتر باشد.')
    if not re.search(r'[0-9]', value):
        raise serializers.ValidationError('رمز عبور باید حداقل یک عدد داشته باشد.')
    if not re.search(r'[a-z]', value):
        raise serializers.ValidationError('رمز عبور باید حداقل یک حرف کوچک انگلیسی داشته باشد.')
    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError('رمز عبور باید حداقل یک حرف بزرگ انگلیسی داشته باشد.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', value):
        raise serializers.ValidationError('رمز عبور باید حداقل یک نماد (مثل !@#$%) داشته باشد.')
    return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'تکرار رمز عبور با رمز جدید یکسان نیست.'})
        user = self.context.get('request').user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'رمز عبور فعلی صحیح نیست.'})
        return attrs


class SerDepartmentList(serializers.ModelSerializer):
    subunits = serializers.SerializerMethodField()

    def get_subunits(self, unit):
        return [{'id': u.id, 'title': u.title} for u in unit.unit_set.all()]

    class Meta:
        model = Unit
        fields = ['id', 'title', 'subunits']


class SerNotification(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class SerUser(serializers.ModelSerializer):
    theme = serializers.SerializerMethodField()
    post_title = serializers.CharField(read_only=True, source='post.title')
    post_level = serializers.CharField(read_only=True, source='post.level')
    page_size = serializers.IntegerField(read_only=True, source='profile.page_size')
    is_deputy = serializers.BooleanField(read_only=True, source='post.is_deputy')
    is_manager = serializers.BooleanField(read_only=True, source='post.is_manager')
    groups = serializers.SerializerMethodField()
    today = serializers.SerializerMethodField()
    unit_list = serializers.SerializerMethodField()
    parent_unit = serializers.SerializerMethodField()
    menu = serializers.SerializerMethodField()
    notifications = serializers.SerializerMethodField()
    is_hr = serializers.SerializerMethodField()

    def get_is_hr(self, obj):
        if obj.groups.filter(name='hr').exists():
            return True
        return False

    def get_theme(self, user):
        if user.theme is not None:
            return {'bg': user.theme.bg_url, 'main': user.theme.main, 'tint1': user.theme.tint1, 'tint2': user.theme.tint2, 'tint3': user.theme.tint3}
        return {'bg': user.bg_url, 'main': user.main, 'tint1': user.tint1, 'tint2': user.tint2, 'tint3': user.tint3}

    def get_today(self, user):
        return str(jdatetime.date.today())

    def get_groups(self, user):
        return [g.name for g in user.groups.all()]

    def get_unit_list(self, user):
        if user.post is None:
            return []
        if user.post.is_deputy or user.groups.filter(name='supervisor').exists():
            unit_list = Unit.objects.filter(parent=None)
        elif user.post.is_deputy:
            unit_list = Unit.objects.filter(id=user.post.unit.parent_id)
        else:
            unit_list = Unit.objects.filter(id=user.post.unit_id)
        return SerDepartmentList(unit_list, many=True).data

    def get_parent_unit(self, user):
        """Returns the topmost parent unit information"""
        if not user.post or not user.post.unit:
            return None

        current_unit = user.post.unit
        # Traverse up the hierarchy to find the root parent unit
        while current_unit.parent:
            current_unit = current_unit.parent

        return current_unit.title

    def get_menu(self, user):
        _list = Menu.objects.filter(Q(levels=[]) | Q(levels__contains=[user.post.level]), Q(groups__isnull=True) | Q(groups__in=user.groups.all()), Q(posts__isnull=True) | Q(posts__in=[user.post]), Q(users__isnull=True) | Q(users__in=[user]))
        if getattr(user, 'post', None) is None:
            _list = _list.filter(should_has_post=True)
        if getattr(user, 'is_interim', True) is True:
            _list = _list.filter(interim_not_allowed=False)
        data = [{
            'key': m.key,
            'title': m.title,
            'todo': getattr(user, f'todo_{m.key}', 0),
            'icon': m.icon
        } for m in _list.distinct()]
        sort_map = {v: i for i, v in enumerate(user.menu_order.split(','))}
        return sorted(data, key=lambda x: sort_map.get(x['key'], len(sort_map)))

    def get_notifications(self, user):
        return []

    class Meta:
        model = User
        fields = [
            'id', 'personnel_code', 'username', 'name', 'photo_url', 'thumbnail_url', 'post_title', 'post_level', 'page_size', 'is_hr',
            'is_head_of_unit', 'is_deputy', 'is_manager', 'is_interim', 'unit', 'parent_unit', 'subunit', 'today', 'notifications', 'mobile', 'menu', 'theme', 'groups', 'unit_list'
        ]


class SerUserList(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name']


class SerUnitList(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'title']


class SerProclamationAppendix(serializers.ModelSerializer):
    class Meta:
        model = ProclamationAppendix
        fields = ['id', 'title', 'file', 'file_url']


class SerProclamationList(serializers.ModelSerializer):
    unit_title = serializers.CharField(read_only=True, source='unit.title')
    seen = serializers.SerializerMethodField()

    def get_seen(self, proclamation):
        return proclamation.proclamationseen_set.filter(user=self.context['user']).exists()

    class Meta:
        model = Proclamation
        fields = ['main_page_order', 'id', 'type', 'title', 'view_count',  'thumbnail_url', 'poster_url','unit_title', '_time', 'seen']


class SerProclamationGallery(serializers.ModelSerializer):
    class Meta:
        model = ProclamationGallery
        fields = ['id', 'file_url']


class SerProclamationDetail(serializers.ModelSerializer):
    unit_name = serializers.CharField(read_only=True, source='unit.title')
    gallery = SerProclamationGallery(read_only=True, many=True)
    appendices = SerProclamationAppendix(read_only=True, many=True)
    create_time = serializers.SerializerMethodField()

    def get_create_time(self, proclamation):
        return proclamation.create_time.strftime('%Y-%m-%d %H:%M')

    class Meta:
        model = Proclamation
        fields = [
            'id', 'type', 'title', 'unit_name', 'view_count',
            'body', 'gallery', 'appendices', 'create_time'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if data['type'] == 'فرانما':
            data['gallery'] = [{
                'id': 1,
                'file_url': 'faranama.png'
            }]

        return data

class SerTellList(serializers.ModelSerializer):
    tell_local = serializers.CharField(read_only=True, source='post.tell_local')
    tell = serializers.CharField(read_only=True, source='post.tell')

    class Meta:
        model = User
        fields = ['id', 'name', 'unit', 'unit_title', 'tell_local', 'tell']


class SerProclamationManage(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source='user.name')
    unit = serializers.CharField(read_only=True, source='unit.title')
    gallery = SerProclamationGallery(read_only=True, many=True)
    appendices = SerProclamationAppendix(read_only=True, many=True)
    create_time = serializers.SerializerMethodField()

    def get_create_time(self, proclamation):
        return proclamation.create_time.strftime('%Y-%m-%d %H:%M')

    class Meta:
        model = Proclamation
        fields = ['id', 'user', 'unit', 'type', 'display_duration', 'title', 'body', 'create_time', 'expire_date', 'seen_count', 'gallery', 'appendices']


class SerTreeChart(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, post):
        return SerTreeChart(post.post_set, many=True).data

    class Meta:
        model = Post
        fields = ['id', 'title', 'level', 'active_user_name', 'active_user_photo', 'children']


class SerThemeList(serializers.ModelSerializer):
    bg = serializers.CharField(read_only=True, source='bg.name')

    class Meta:
        model = Theme
        fields = ['id', 'title', 'bg', 'main', 'tint1', 'tint2', 'tint3']
