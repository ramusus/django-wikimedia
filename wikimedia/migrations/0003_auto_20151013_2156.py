# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wikimedia', '0002_auto_20151013_2156'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='wikipage',
            unique_together=set([('lang', 'project', 'title')]),
        ),
    ]
