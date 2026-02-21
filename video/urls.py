from django.urls import path
from video import views

app_name = 'video'

urlpatterns = [
    # Video URLs
    path('', views.VideoListCreateView.as_view(), name='video-list-create'),
    path('v2/', views.VideoListCreateViewV2.as_view(), name='video-list-create-v2'),

    # path('ex/', views.add_videos, name='add'),
    path('<int:pk>/', views.VideoDetailView.as_view(), name='video-detail'),
    path('<int:pk>/like/', views.VideoLikeView.as_view(), name='video-like'),

    # Comment URLs
    path('<int:pk>/comments/', views.VideoCommentListCreateView.as_view(), name='video-comment-list-create'),
    path('<int:pk>/comments/<int:comment_pk>/', views.VideoCommentDetailView.as_view(), name='video-comment-detail'),

    # Category and Tag URLs
    path('categories/', views.VideoCategoryListView.as_view(), name='video-category-list'),
    path('tags/', views.VideoTagListView.as_view(), name='video-tag-list'),

    # Stats and Analytics URLs
    path('stats/', views.video_stats, name='video-stats'),
    path('trending/', views.trending_videos, name='trending-videos'),
    path('my-videos/', views.user_videos, name='user-videos'),
    path('liked-videos/', views.liked_videos, name='liked-videos'),
]
