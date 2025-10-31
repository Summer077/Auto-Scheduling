# Generated migration for adding color field to Course model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='color',
            field=models.CharField(default='#FFA726', max_length=7),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]