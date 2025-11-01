from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0005_faculty_room_activity_section_schedule'),  # Change to your last migration
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='duration',
            field=models.IntegerField(default=0, help_text='Duration in minutes'),
        ),
    ]