from rest_framework import serializers
from django.contrib.auth import get_user_model
from video.models import Video, VideoLike, VideoComment, VideoCategory, VideoTag, VideoCategoryRelation, VideoTagRelation, VideoFileAppendix

User = get_user_model()


class VideoFileAppendixSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = VideoFileAppendix
        fields = ['id', 'title', 'file']

    def get_file(self, obj):
        return obj.file.name


# class VideoFileAppendixSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = VideoFileAppendix
#        fields = ['id', 'title', 'file']
#        read_only_fields = ['id']


class VideoFileAppendixCreateSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد فایل پیوست در API ایجاد ویدیو"""

    class Meta:
        model = VideoFileAppendix
        fields = ['title', 'file']


class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ['id', 'name', 'description', 'created_at']


class VideoTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoTag
        fields = ['id', 'name', 'created_at']


class VideoUploaderSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', "photo_url"]

    def get_first_name(self, obj):
        return "پژوهشگاه فضای مجازی"

    def get_last_name(self, obj):
        return ""


class CommentUploaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'photo_url']


class VideoCommentSerializer(serializers.ModelSerializer):
    user = CommentUploaderSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VideoComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at', 'is_approved', 'replies']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_created_at(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%m') if obj.created_at else None

    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True).order_by('created_at')
        return VideoCommentSerializer(replies, many=True).data


class VideoLikeSerializer(serializers.ModelSerializer):
    user = VideoUploaderSerializer(read_only=True)

    class Meta:
        model = VideoLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']


class VideoListSerializer(serializers.ModelSerializer):
    uploader = VideoUploaderSerializer(read_only=True)
    categories = VideoCategorySerializer(source='videocategoryrelation_set.category', many=True, read_only=True)
    tags = VideoTagSerializer(source='videotagrelation_set.tag', many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    released_at = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()

    preview_file = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'poster', 'video_file', 'preview_file',
            'uploader', 'created_at', 'updated_at', 'is_published', 'released_at',
            'view_count', 'like_count', 'comment_count', 'categories', 'tags', 'is_liked'
        ]

    def get_poster(self, obj):
        return obj.poster.name if obj.poster else None

    def get_released_at(self, obj):
        return obj.created_at.strftime('%Y/%m/%d') if obj.created_at else None

    def get_video_file(self, obj):
        return obj.video_file.name if obj.video_file else None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_preview_file(self, obj):
        return obj.preview_file.name if obj.preview_file else None


class VideoDetailSerializer(serializers.ModelSerializer):
    uploader = VideoUploaderSerializer(read_only=True)
    categories = VideoCategorySerializer(source='videocategoryrelation_set.category', many=True, read_only=True)
    tags = VideoTagSerializer(source='videotagrelation_set.tag', many=True, read_only=True)
    comments = VideoCommentSerializer(many=True, read_only=True)
    likes = VideoLikeSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    released_at = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()
    appendices = VideoFileAppendixSerializer(source="files", many=True, read_only=True)
    preview_file = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'poster', 'video_file', 'preview_file',
            'uploader', 'created_at', 'updated_at', 'is_published', 'released_at',
            'view_count', 'like_count', 'comment_count', 'categories',
            'tags', 'comments', 'likes', 'is_liked', 'appendices'
        ]

    def get_preview_file(self, obj):
        return obj.preview_file.name if obj.preview_file else None

    def get_poster(self, obj):
        return obj.poster.name if obj.poster else None

    def get_video_file(self, obj):
        return obj.video_file.name if obj.video_file else None

    def get_released_at(self, obj):
        return obj.created_at.strftime('%Y/%m/%d') if obj.created_at else None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class VideoCreateSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), write_only=True, required=False)
    appendixes = VideoFileAppendixCreateSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'poster', 'video_file', 'preview_file',
            'is_published', 'categories', 'tags', 'appendixes'
        ]

    def create(self, validated_data):
        categories_data = validated_data.pop('categories', [])
        tags_data = validated_data.pop('tags', [])
        appendixes_data = validated_data.pop('appendixes', [])

        # Set the uploader to the current user
        validated_data['uploader'] = self.context['request'].user
        validated_data['is_published'] = True
        video = Video.objects.create(**validated_data)

        # Add categories
        for category_id in categories_data:
            try:
                category = VideoCategory.objects.get(id=category_id)
                VideoCategoryRelation.objects.create(video=video, category=category)
            except VideoCategory.DoesNotExist:
                pass

        # Add tags
        for tag_name in tags_data:
            tag, created = VideoTag.objects.get_or_create(name=tag_name)
            VideoTagRelation.objects.create(video=video, tag=tag)

        # Add file appendixes
        for appendix_data in appendixes_data:
            VideoFileAppendix.objects.create(video=video, **appendix_data)

        return video

    def update(self, instance, validated_data):
        categories_data = validated_data.pop('categories', None)
        tags_data = validated_data.pop('tags', None)
        appendixes_data = validated_data.pop('appendixes', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.is_published = True
        instance.save()

        # Update categories if provided
        if categories_data is not None:
            instance.videocategoryrelation_set.all().delete()
            for category_id in categories_data:
                try:
                    category = VideoCategory.objects.get(id=category_id)
                    VideoCategoryRelation.objects.create(video=instance, category=category)
                except VideoCategory.DoesNotExist:
                    pass

        # Update tags if provided
        if tags_data is not None:
            instance.videotagrelation_set.all().delete()
            for tag_name in tags_data:
                tag, created = VideoTag.objects.get_or_create(name=tag_name)
                VideoTagRelation.objects.create(video=instance, tag=tag)

        # Update file appendixes if provided
        if appendixes_data is not None:
            instance.views.all().delete()  # Note: related_name is 'views' in the model
            for appendix_data in appendixes_data:
                VideoFileAppendix.objects.create(video=instance, **appendix_data)

        return instance


class VideoCommentCreateSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()


    class Meta:
        model = VideoComment
        fields = ['content', 'parent', "created_at", "updated_at"]

    def get_created_at(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%m') if obj.created_at else None

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['video'] = self.context['video']
        return super().create(validated_data)


class VideoLikeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLike
        fields = []

    def create(self, validated_data):
        user = self.context['request'].user
        video = self.context['video']

        like, created = VideoLike.objects.get_or_create(
            user=user,
            video=video
        )

        if not created:
            like.delete()
            video.update_like_count()
            return None

        video.update_like_count()
        return like


class VideoCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ['name', 'description']


class VideoTagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoTag
        fields = ['name']
