# Generated migration to add timestamp fields to Material model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='material',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='material',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
