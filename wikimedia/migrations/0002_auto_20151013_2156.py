# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wikimedia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wikipage',
            name='lang',
            field=models.CharField(db_index=True, max_length=2, verbose_name='Language', choices=[(b'ru', b'Russian'), (b'en', b'English')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wikipage',
            name='title',
            field=models.CharField(max_length=300, verbose_name='Title', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wikipage',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Date and time of last updating', db_index=True),
            preserve_default=True,
        ),
    ]
