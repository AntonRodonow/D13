from django.apps import AppConfig
import redis #установка redis


class NewappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'newapp'

    def ready(self):
        import newapp.signals
        from .tasks import weekly_digest
        from newapp.management.commands.runapscheduler import my_job

# установка redis, сейчас не надо, надо разобраться когда это требуется и в какой app.py ложить
# red = redis.Redis(
#     host='redis-18644.c1.ap-southeast-1-1.ec2.cloud.redislabs.com',
#     port=18644,
#     password='KwLEgp1AykxtqKTeYKFlCvoT6fniFCSJ'
# )