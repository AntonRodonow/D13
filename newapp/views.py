from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Post, Category, BaseRegisterForm
from .filters import PostFilter
from .forms import PostForm
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

class PostList(ListView):
    model = Post
    template_name = 'posts.html'
    context_object_name = 'news'
    queryset = Post.objects.order_by('-id')
    paginate_by = 3
    form_class = PostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())
        context['categories'] = Category.objects.all()
        context['form'] = PostForm()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
        return super().get(request, *args, **kwargs)

class PostDetailView(DetailView):               # работает дженерик для деталей новостей
    template_name = 'newapp/post_detail.html'
    queryset = Post.objects.all()
    context_object_name = 'new'

class PostAddView(PermissionRequiredMixin, CreateView):              # работает дженерик создания новостей
    permission_required = ('newapp.add_post',) # тест
    template_name = 'newapp/post_add.html'
    form_class = PostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_authors'] = not self.request.user.groups.filter(name='authors').exists()
        return context

# class PostDetail(DetailView):          # скорее всего уже не понадобится
    # model = Post
    # template_name = 'post.html'
    # context_object_name = 'new'

class PostListFilter(ListView):
    model = Post
    template_name = 'postsfilter.html'
    context_object_name = 'news'
    queryset = Post.objects.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())
        # context['categories'] = Category.objects.all()
        # context['form'] = PostForm()
        return context

# class PostUpdateView(UpdateView):
class PostUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):     # дженерик для редактирования новостей
    permission_required = ('newapp.change_post',)                   # ограничение прав на изм. новостей
    template_name = 'newapp/post_add.html'                          # (без TemplateView работает как часы)
    form_class = PostForm                                           # LoginRequiredMixin запрещ доступ для не зарегистр. польз.

    # метод get_object мы используем вместо queryset, чтобы получить информацию об объекте, который мы собираемся редактировать
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)


class PostDeleteView(LoginRequiredMixin, DeleteView):            # дженерик для удаления новостей
    template_name = 'newapp/post_delete.html'
    queryset = Post.objects.all()
    success_url = '/news/'


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/news/'  # проверка работы

@login_required
def upgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)
    return redirect('/news/')


# в админ панели создали данные ограничения,
# если пользователь не входит в нужную группу, ему летает страница с ошибкой 403 (страница недоступна)
# Существует определенное соглашение для именования разрешений: <app>.<action>_<model>,
# После того, как мы написали наши ограничения, нужно в urls изменить выводы преставлений,указав на новые классы (ниже):

# class AddNews(PermissionRequiredMixin, PostAddView):  # мы сделали не отдельным классом а в уже существующем
#     permission_required = ('newapp.add_post',)


# class ChangeNews(PermissionRequiredMixin, PostUpdateView):    # мы сделали не отдельным классом а в уже существующем
#     permission_required = ('newapp.change_post',)

