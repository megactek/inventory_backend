# Generated by Django 4.1.2 on 2022-11-28 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_control", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="last_login",
            field=models.DateTimeField(null=True),
        ),
    ]
