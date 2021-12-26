from django.forms import ModelForm
from .models import Post
from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group


# Создаём модельную форму
class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['author', 'categoryType', 'postCategory', 'title', 'text', 'rating']


class CommonSignupForm(SignupForm):  # переопределил этот класс на .models (class BaseRegisterForm(UserCreationForm))

    def save(self, request):
        user = super(CommonSignupForm, self).save(request)
        common_group = Group.objects.get(name='common')
        common_group.user_set.add(user)
        return user
