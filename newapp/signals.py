
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import mail_managers

from .models import Post, Category, User



# created - булевая, есть или нет объект в БД
@receiver(post_save, sender=Post)
def notify_managers_post(sender, instance, created, **kwargs):
    count = 0
    user_aut = instance.author
    print(f"{user_aut}")
    print('Test 2')

    if created:
        subject = f'Подоспела новая публикация {instance.title} от {instance.author} : {instance.dateCreation.strftime("%d %m %Y")}'
    else:
        subject = f'Была актуализирована публикация {instance.title} от {instance.author} : {instance.dateCreation.strftime("%d %m %Y")}'
    all_email_to = ['anrodion81222@yandex.ru',] # добавлен адрес админа, но можно и пустой список
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

    print('Разослано!')