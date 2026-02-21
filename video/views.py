from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from video.models import Video, VideoLike, VideoComment, VideoCategory, VideoTag, VideoView, VideoFileAppendix
from video.serializers import (
    VideoListSerializer, VideoDetailSerializer, VideoCreateSerializer,
    VideoCommentSerializer, VideoCommentCreateSerializer, VideoLikeCreateSerializer,
    VideoCategorySerializer, VideoTagSerializer, VideoCategoryCreateSerializer,
    VideoTagCreateSerializer
)
from core.models import HdPagination


class VideoListCreateViewV2(generics.ListCreateAPIView):
    """لیست ویدیوها و ایجاد ویدیو جدید"""
    queryset = Video.objects.filter(is_published=True).order_by('-created_at')
    pagination_class = HdPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoCreateSerializer
        return VideoListSerializer

    def get_queryset(self):
        queryset = Video.objects.filter().order_by('-id')

        # فیلتر بر اساس دسته‌بندی
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(videocategoryrelation__category__name__icontains=category)

        # فیلتر بر اساس تگ
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(videotagrelation__tag__name__icontains=tag)

        # جستجو در عنوان و توضیحات
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # مرتب‌سازی
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ['created_at', '-created_at', 'view_count', '-view_count', 'like_count', '-like_count']:
            queryset = queryset.order_by(ordering)

        return queryset.select_related('uploader').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        appendixes_data = request.FILES.getlist('append_file')  # یا هر نامی که تو Postman فرستادی
        appendixes_titles = request.data.getlist('append_title')  # یا هر نامی که تو Postman فرستادی

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save()

        return Response(self.get_serializer(video).data, status=status.HTTP_201_CREATED)


class VideoListCreateView(generics.ListCreateAPIView):
    """لیست ویدیوها و ایجاد ویدیو جدید"""
    queryset = Video.objects.filter(is_published=True).order_by('-created_at')[0:12]
    permission_classes = [IsAuthenticated]

    #    pagination_class = HdPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoCreateSerializer
        return VideoListSerializer

    def get_queryset(self):
        queryset = Video.objects.filter().order_by('id')

        # فیلتر بر اساس دسته‌بندی
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(videocategoryrelation__category__name__icontains=category)

        # فیلتر بر اساس تگ
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(videotagrelation__tag__name__icontains=tag)

        # جستجو در عنوان و توضیحات
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # مرتب‌سازی
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ['created_at', '-created_at', 'view_count', '-view_count', 'like_count', '-like_count']:
            queryset = queryset.order_by(ordering)

        return queryset.select_related('uploader').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        appendixes_data = request.FILES.getlist('append_file')  # یا هر نامی که تو Postman فرستادی
        appendixes_title = request.data.getlist('append_title')  # یا هر نامی که تو Postman فرستادی

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save()
        for append in zip(appendixes_data, appendixes_title):
            append_instance = VideoFileAppendix.objects.create(video=video, title=append[1], file=append[0])

        return Response(self.get_serializer(video).data, status=status.HTTP_201_CREATED)


class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات ویدیو، ویرایش و حذف"""
    queryset = Video.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VideoCreateSerializer
        return VideoDetailSerializer

    def get_object(self):
        obj = get_object_or_404(Video, pk=self.kwargs['pk'])

        # فقط مالک یا ادمین
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.uploader != self.request.user and not self.request.user.is_staff:
                self.permission_denied(self.request)

        # افزایش بازدید فقط در GET
        if self.request.method == 'GET':
            obj.increment_view_count(self.request.user)

        return obj

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # ✅ سریالایزر برای آپدیت
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'video_file' in request.FILES:
            if instance.video_file:
                instance.video_file.delete(save=False)
            instance.video_file = request.FILES['video_file']
            instance.save(update_fields=['video_file'])

        if 'preview_file' in request.FILES:
            if instance.preview_file:
                instance.preview_file.delete(save=False)
            instance.preview_file = request.FILES['preview_file']
            instance.save(update_fields=['preview_file'])

        if 'poster' in request.FILES:
            if instance.poster:
                instance.poster.delete(save=False)
            instance.poster = request.FILES['poster']
            instance.save(update_fields=['poster'])

        serializer.save()

        # ✅ مدیریت فایل‌های ضمیمه (appendixes)
        appendixes_data = request.FILES.getlist('append_file', [])
        appendixes_title = request.data.getlist('append_title', [])
        appendices_ids = request.data.getlist('appendices', [])

        # حذف ضمیمه‌هایی که حذف شدن
        for ap in VideoFileAppendix.objects.filter(video=instance):
            if str(ap.pk) not in appendices_ids:
                ap.file.delete(save=False)  # حذف از استوریج
                ap.delete()

        # اضافه کردن ضمیمه‌های جدید
        for file_obj, title in zip(appendixes_data, appendixes_title):
            VideoFileAppendix.objects.create(video=instance, title=title, file=file_obj)

        # ✅ فایل ویدیو اصلی اگر فرستاده شد، جایگزین کن
        #        if 'video_file' in request.FILES:
        #            #if instance.video_file:
        #                #instance.video_file.delete(save=False)
        #            instance.video_file = request.FILES['video_file']
        #            instance.save(update_fields=['video_file'])

        #        if 'preview_file' in request.FILES:
        #            #if instance.preview_file:
        #            #    instance.preview_file.delete(save=False)
        #            instance.preview_file = request.FILES['preview_file']
        #            instance.save()

        #        if 'poster' in request.FILES:
        #            #if instance.poster:
        #            #    instance.poster.delete(save=False)
        #            instance.poster = request.FILES['poster']
        #            instance.save(update_fields=['poster'])

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)


class VVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات ویدیو، ویرایش و حذف"""
    queryset = Video.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VideoCreateSerializer
        return VideoDetailSerializer

    def get_object(self):
        obj = get_object_or_404(Video, pk=self.kwargs['pk'])

        # فقط مالک ویدیو یا ادمین می‌تواند ویرایش/حذف کند
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.uploader != self.request.user and not self.request.user.is_staff:
                self.permission_denied(self.request)

        # افزایش تعداد بازدید برای درخواست‌های GET
        if self.request.method == 'GET':
            obj.increment_view_count(self.request.user)

        return obj

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        appendixes_data = request.FILES.getlist('append_file')  # یا هر نامی که تو Postman فرستادی
        appendixes_title = request.data.getlist('append_title')  # یا هر نامی که تو Postman فرستادی

        appendices = request.data.getlist('appendices')
        video_appends = VideoFileAppendix.objects.filter(video=instance)
        for ap in video_appends:
            if str(ap.pk) not in appendices:
                ap.delete()

        # serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = self.perform_update(serializer)
        for append in zip(appendixes_data, appendixes_title):
            append_instance = VideoFileAppendix.objects.create(video=instance, title=append[1], file=append[0])

        return Response(self.get_serializer(video).data, status=status.HTTP_201_CREATED)


class VideoLikeView(generics.GenericAPIView):
    """لایک/آنلایک ویدیو"""
    serializer_class = VideoLikeCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """لایک کردن ویدیو"""
        video = get_object_or_404(Video, pk=kwargs['pk'])

        try:
            like = VideoLike.objects.get(user=request.user, video=video)
            like.delete()
            video.update_like_count()
            return Response({'message': 'لایک حذف شد'}, status=status.HTTP_200_OK)
        except VideoLike.DoesNotExist:
            like = VideoLike.objects.create(user=request.user, video=video)
            video.update_like_count()
            serializer = VideoLikeCreateSerializer(like, context={'request': request, 'video': video})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """حذف لایک (آنلایک)"""
        video = get_object_or_404(Video, pk=kwargs['pk'])

        try:
            like = VideoLike.objects.get(user=request.user, video=video)
            like.delete()
            video.update_like_count()
            return Response({'message': 'لایک حذف شد'}, status=status.HTTP_200_OK)
        except VideoLike.DoesNotExist:
            return Response({'message': 'لایک یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class VideoCommentListCreateView(generics.ListCreateAPIView):
    """لیست کامنت‌ها و ایجاد کامنت جدید"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoCommentCreateSerializer
        return VideoCommentSerializer

    def get_queryset(self):
        video = get_object_or_404(Video, pk=self.kwargs['pk'])
        return VideoComment.objects.filter(
            video=video,
            is_approved=True,
            parent__isnull=True
        ).select_related('user').prefetch_related('replies__user').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        video = get_object_or_404(Video, pk=kwargs['pk'])
        serializer = VideoCommentCreateSerializer(
            data=request.data,
            context={'request': request, 'video': video}
        )

        if serializer.is_valid():
            comment = serializer.save()
            video.update_comment_count()

            c = VideoComment.objects.filter(id=comment.id).first()
            return Response(VideoCommentSerializer(c).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VideoCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات کامنت، ویرایش و حذف"""
    serializer_class = VideoCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VideoComment.objects.all()

    def get_object(self):
        obj = get_object_or_404(VideoComment, pk=self.kwargs['comment_pk'])

        # فقط مالک کامنت یا ادمین می‌تواند ویرایش/حذف کند
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.user != self.request.user and not self.request.user.is_staff:
                self.permission_denied(self.request)

        return obj

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        video = comment.video
        comment.delete()
        video.update_comment_count()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideoCategoryListView(generics.ListCreateAPIView):
    """لیست دسته‌بندی‌ها و ایجاد دسته‌بندی جدید"""
    permission_classes = [IsAuthenticated]

    queryset = VideoCategory.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoCategoryCreateSerializer
        return VideoCategorySerializer


class VideoTagListView(generics.ListCreateAPIView):
    """لیست تگ‌ها و ایجاد تگ جدید"""
    permission_classes = [IsAuthenticated]

    queryset = VideoTag.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoTagCreateSerializer
        return VideoTagSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def video_stats(request):
    """آمار کلی ویدیوها"""
    stats = {
        'total_videos': Video.objects.filter(is_published=True).count(),
        'total_views': Video.objects.filter(is_published=True).aggregate(
            total_views=Sum('view_count')
        )['total_views'] or 0,
        'total_likes': Video.objects.filter(is_published=True).aggregate(
            total_likes=Sum('like_count')
        )['total_likes'] or 0,
        'total_comments': Video.objects.filter(is_published=True).aggregate(
            total_comments=Sum('comment_count')
        )['total_comments'] or 0,
    }
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_videos(request):
    """ویدیوهای ترند"""
    from datetime import datetime, timedelta

    # ویدیوهای محبوب در 7 روز گذشته
    week_ago = datetime.now() - timedelta(days=7)
    trending = Video.objects.filter(
        is_published=True,
        created_at__gte=week_ago
    ).order_by('-like_count', '-view_count')[:10]

    serializer = VideoListSerializer(trending, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_videos(request):
    """ویدیوهای کاربر"""
    videos = Video.objects.filter(uploader=request.user).order_by('-created_at')
    serializer = VideoListSerializer(videos, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liked_videos(request):
    """ویدیوهای لایک شده توسط کاربر"""
    liked_videos = Video.objects.filter(
        likes__user=request.user,
        is_published=True
    ).order_by('-likes__created_at')

    serializer = VideoListSerializer(liked_videos, many=True, context={'request': request})
    return Response(serializer.data)





