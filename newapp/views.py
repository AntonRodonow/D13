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
from django.core.mail import mail_managers
from django.dispatch import receiver
from django.db.models.signals import post_save
from .tasks import hello, weekly_digest_celery, notify_subscribers

#celery test

def index (request):
    hello.delay()
    return render(request, 'index.html')
#end celery test



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

@receiver(post_save, sender=Post)
def notify_managers_post(sender, instance, created, **kwargs):
    count = 0
    user_aut = instance.author
    print(f"{user_aut}")
    print('Test 2')

    if created:
        subject = f'Подоспела новая публикация {instance.title} от {instance.author}'
    else:
        subject = f'Была актуализирована публикация {instance.title} от {instance.author}'
    all_email_to = ['anrodion81222@yandex.ru',]
    for category in instance.postCategory.all():
        print(f'{category}')
        for user in category.subscribers.all():
            user.email
            all_email_to.append(user.email)

    print(f'{all_email_to}')

    send_mail(subject=subject,
              message=instance.text[:40],
              from_email='anrodion81222@yandex.ru',
              recipient_list=all_email_to)

# celery and redis
@receiver(post_save, sender=Post)
def notify_managers_post(sender, instance, created, **kwargs):
    user_aut = instance.author
    print(f"{user_aut}")

    if created:
        subject = f'Подоспела новая публикация {instance.title} от {instance.author}'
    else:
        subject = f'Была актуализирована публикация {instance.title} от {instance.author}'
    all_email_to = ['anrodion81222@yandex.ru',]
    all_user_names_to = []
    for category in instance.postCategory.all():
        print(f'{category}')
        for user in category.subscribers.all():
            # user.email #это лишнее!!!
            all_email_to.append(user.email)
            all_user_names_to.append(user.username)
            sub_name = user.username
            sub_email = user.email
            title = instance.title
            pub_time = instance.dateCreation.strftime("%d %m %Y")
            pk = instance.pk
            # post = Post.objects.get(id=pk) # лишнее
            category = Post.objects.get(id=pk).postCategory.get().name

            notify_subscribers.delay(sub_name, sub_email, title, category, pub_time, pk) # отправлена задача celery

    print(f'{all_email_to}')

    send_mail(subject=subject,
              message=instance.text[:40],
              from_email='anrodion81222@yandex.ru',
              recipient_list=all_email_to)


class PostAddView(PermissionRequiredMixin, CreateView):              # дженерик создания новостей
    model = Post
    print(f'Test 1')
    permission_required = ('newapp.add_post',)
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
    template_name = 'newapp/post_add.html'
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


class CategoryView(FormView, View, Category):  # добавил View, Category, Post вероятно не нужны!!!!!
    form_class = CategorySubscribers
    template_name = 'newapp/subscribers.html'
    success_url = '/news/'

    def form_valid(self, form):
        user = self.request.user
        category_id = self.request.POST['category']
        category = Category.objects.get(pk=category_id)
        category.subscribers.add(user)
        # category.save() # это не нужно
        print(f'{user} {category.subscribers.all()}')
        return super().form_valid(form)


# Если пользователь подписан на какую-либо категорию,
# то, как только в неё добавляется новая статья, её краткое содержание приходит пользователю на электронную почту,
# которую он указал при регистрации. В письме обязательно должна быть гиперссылка на саму статью,
# чтобы он мог по клику перейти и прочитать её.

# будет приходить письмо с HTML-кодом заголовка и первых 50 символов текста статьи
# В теме письма должен быть сам заголовок статьи. Текст состоит из вышеуказанного HTML и текста:
# «Здравствуй, username. Новая статья в твоём любимом разделе!».

# текст и заголов находится Post.text (models), в html - ххх.text|truncatechars:50|censor, заголовок - new.title|censor,





# @login_required   # еще один способ на заметку
# def add_subscribe(request, pk):
#
#     user = request.user
#
#     # category_object = PostCategory.objects.get(category=pk)
#     id_u = user.id
#     category = Category.objects.get(id=pk)
#     # category.subscribers.add(user)
#     print(f'''PK =  "{pk}", USER:  "{user}", user_id: "{id_u}", category: "{category}"''')
#
#     qs = category.subscribers.all()
#     print('QS= ', qs)
#     print('ПОДПИСАН НА КАТЕГОРИЮ ? ', qs.filter(username=user).exists())
#     # print(category_object)
#     # print(Category.objects.all().filter(postcategory=category))
#     # .Post.category.category.subscribers.objects.all().user.username
#     if not qs.filter(username=user).exists():
#         category.subscribers.add(user)
#         print('Пользователь', user, 'подписан на категорию:', category)
#     else:
#         category.subscribers.remove(user)
#         print('Пользователь', user, 'отписался от категории:', category)
#
#     # print('ПОДПИСЧИКИ: ', category.subscribers.all())
#
#     try:
#         email = category.subscribers.get(id=id_u).email
#         print(f'''email: "{email}" Можно отправить уведомление''')
#         send_mail(
#             subject=f'News Portal: подписка на обновления категории {category}',
#             message=f'«{request.user}», вы подписались на обновление категории: «{category}».',
#             from_email='apractikant@yandex.ru',
#             recipient_list=[f'{email}', ],
#         )
#
#     except Exception as n:
#         print('nnnnnnnnnnnnnnnnnnnnn')
#     # Category.objects.get(pk=pk).subscribers.add(request.user)
#     # print(category.subscribers.all())
#     return redirect('/')

#celery and redis task
def weekly_celery_redis (request):
    weekly_digest_celery.delay()
    print('Complete')
#end celery and redis task
