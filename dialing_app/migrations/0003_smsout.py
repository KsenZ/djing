# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-01-04 18:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dialing_app', '0002_auto_20171229_1353'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSOut',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True, verbose_name='When')),
                ('dst', models.CharField(max_length=16, verbose_name='Telephone')),
                ('text', models.CharField(max_length=255, verbose_name='Text')),
                ('status', models.CharField(choices=[('nw', 'New'), ('st', 'Sent'), ('fd', 'Failed')], default='nw', max_length=2, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Out SMS',
                'verbose_name_plural': 'Out SMS',
                'db_table': 'out_sms',
                'permissions': (('can_view_sms', 'Can view sms'), ('can_send_sms', 'Can send sms')),
            },
        ),
    ]
