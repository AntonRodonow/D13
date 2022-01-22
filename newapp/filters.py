from django_filters import FilterSet, DateFromToRangeFilter
from .models import Post


class PostFilter(FilterSet):
    dateCreation = DateFromToRangeFilter()
    class Meta:
         model = Post
         fields = ['dateCreation', 'author']




