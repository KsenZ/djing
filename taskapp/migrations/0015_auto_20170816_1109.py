# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-08-16 11:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0014_auto_20170416_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changelog',
            name='act_type',
            field=models.CharField(choices=[('e', 'Изменение задачи'), ('c', 'Создание задачи'), ('d', 'Удаление задачи'), ('f', 'Завершение задачи'), ('b', 'Задача провалена')], max_length=1),
        ),
        migrations.AlterField(
            model_name='task',
            name='state',
            field=models.CharField(choices=[('S', 'Новая'), ('C', 'Провалена'), ('F', 'Выполнена')], default='S', max_length=1),
        ),
    ]
