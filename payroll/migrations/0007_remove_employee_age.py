# Generated by Django 5.1.7 on 2025-04-02 18:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0006_employee_address_employee_date_joined_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='age',
        ),
    ]
