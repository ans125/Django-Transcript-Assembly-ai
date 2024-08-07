from django.urls import path
from . import views

urlpatterns = [
    path('index', views.index, name='index'),
    path('', views.main, name='main'),
    path('login', views.user_login, name='login'),
    path('signup', views.user_signup, name='signup'),
    path('logout', views.user_logout, name='logout'),
    path('generate-blog', views.generate_blog, name='generate-blog'),
    path('blog-list', views.blog_list, name='blog-list'),
    path('blog-details/<int:pk>/', views.blog_details, name='blog-details'),
    path('download', views.download, name='download'),
    path('translate-content', views.translate_content, name='translate-content'),  # Add this line
]
