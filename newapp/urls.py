from django.urls import path
from .views import PostList, PostDetailView, PostAddView, PostListFilter, PostUpdateView, PostDeleteView, \
    BaseRegisterView, upgrade_me
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', PostList.as_view()),
    path('<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('add/', PostAddView.as_view(), name='post_add'),
    path('search/', PostListFilter.as_view()),
    path('add/', PostUpdateView.as_view(), name='post_update'),  # миксин не задействован при добавлении новости
    path('<int:pk>/edit/', PostUpdateView.as_view(), name='post_update'),  # c миксиным на логирование задействован при редактировании
    path('<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('login/', LoginView.as_view(template_name = 'newapp/login.html'), name='login'),
    path('add/newapp/logout/', LogoutView.as_view(template_name = 'newapp/logout.html'), name='logout'),
    path('signup/', BaseRegisterView.as_view(template_name = 'newapp/signup.html'), name='signup'),
    path('upgrade/', upgrade_me, name='upgrade'),
    path('/news/login/',LoginView.as_view(template_name = 'newapp/login.html'), name='login'),     # не получается переопределить авто пути
]
