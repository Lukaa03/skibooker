from django.db import migrations
from django.utils import timezone


def create_admin(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin@skibooker.rs').exists():
        User.objects.create_superuser(
            first_name='admin',
            username='admin@skibooker.rs',
            email='admin@skibooker.rs',
            password='admin123',
            last_login=timezone.now()
        )

def remove_admin(apps, schema_editor):
    from django.contrib.auth import get_user_model
    get_user_model().objects.filter(username='admin@skibooker.rs').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_alter_businessprofile_id_alter_businessrequest_id_and_more'),
    ]
    operations = [
        migrations.RunPython(create_admin, remove_admin),
    ]