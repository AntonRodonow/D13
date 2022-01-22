from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, reverse, redirect
from django.core.paginator import Paginator
from .models import Post, Category, BaseRegisterForm
from .filters import PostFilter
from .forms import PostForm, CategorySubscribers
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView
from django.core.mail import send_mail, EmailMultiAlternatives
from django.views import View
from django.template.loader import render_to_string


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
    success_url = '/news/'

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

class CategoryView(FormView, View, Category):  # обавил View, Category, Post вероятно не нужны!!!!!
    form_class = CategorySubscribers
    template_name = 'newapp/subscribers.html'
    success_url = '/news/'   # скорректировать позже!!!!!!!!!!!!

    def form_valid(self, form):
        user = self.request.user
        category_id = self.request.Post['category']
        category = Category.objects.get(pk=category_id)
        category.subscribers_set.add(user)
        category.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        # user = request.user
        # email = request.POST['email']
        # category = request.POST['category']
        # subscriber = Post
        subscriber = Post(   # self.request. добавил ///// Category вместо Post
            text=request.POST['text'],
            title=request.POST['title'],
        )
        subscriber.save()

        html_content = render_to_string('newapp/subscriber_created.html',
                                        {'subscriber': subscriber},
                                        )

        msg = EmailMultiAlternatives(
            subject=f'{subscriber.title}',
            body=f'{subscriber.text}',
            from_email='anrodion8122@yandex.ru',
            to=['anrodion8122@yandex.ru', 'anrodion812@gmail.com', request.user.email]
        )

        msg.attach_alternative(html_content, 'Спасибо за подписку!')
        msg.send()

        # send_mail(
        #     subject=f'{subscriber.title}',   # тема письма
        #     message=subscriber.text,
        #     recipient_list=['anrodion8122@yandex.ru',]
        # )
        return redirect('subscribers:make_subscriber')


# Если пользователь подписан на какую-либо категорию,
# то, как только в неё добавляется новая статья, её краткое содержание приходит пользователю на электронную почту,
# которую он указал при регистрации. В письме обязательно должна быть гиперссылка на саму статью,
# чтобы он мог по клику перейти и прочитать её.

# будет приходить письмо с HTML-кодом заголовка и первых 50 символов текста статьи
# В теме письма должен быть сам заголовок статьи. Текст состоит из вышеуказанного HTML и текста:
# «Здравствуй, username. Новая статья в твоём любимом разделе!».

# текст и заголов находится Post.text (models), в html - ххх.text|truncatechars:50|censor, заголовок - new.title|censor,
#

class CategoryView2(FormView, View, Category):  # обавил View, Category, Post вероятно не нужны!!!!!
    template_name = 'newapp/subscribers2.html'
    success_url = '/news/'   # скорректировать позже!!!!!!!!!!!!

    def form_valid(self, form):
        user = self.request.user
        category_id = self.request.Post['category']
        category = Category.objects.get(pk=category_id)
        category.subscribers_set.add(user)
        category.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        # user = request.user
        # email = request.POST['email']
        # category = request.POST['category']
        # subscriber = Post
        subscriber = Post(   # self.request. добавил ///// Category вместо Post
            text=request.POST['text'],
            title=request.POST['title'],
        )
        subscriber.save()

        html_content = render_to_string('newapp/subscriber_created.html',
                                        {'subscriber': subscriber},
                                        )

        msg = EmailMultiAlternatives(
            subject=f'{subscriber.title}',
            body=f'{subscriber.text}',
            from_email='anrodion8122@yandex.ru',
            to=['anrodion8122@yandex.ru', 'anrodion812@gmail.com', request.user.email]
        )

        msg.attach_alternative(html_content, 'Спасибо за подписку!')
        msg.send()

        return redirect('subscribers:make_subscriber')
