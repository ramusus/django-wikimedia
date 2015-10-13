# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wikipage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lang', models.CharField(max_length=2, verbose_name='Language', choices=[(b'ru', b'Russian'), (b'en', b'English')])),
                ('title', models.CharField(max_length=300, verbose_name='Title')),
                ('content', models.TextField(verbose_name='Content')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Date and time of last updating')),
                ('object_id', models.PositiveIntegerField(null=True)),
                ('content_type', models.ForeignKey(related_name='wikipages', to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('-updated',),
                'get_latest_by': 'updated',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Wikiproject',
            fields=[
                ('code', models.CharField(max_length=20, serialize=False, verbose_name='Name', primary_key=True)),
                ('domain', models.CharField(max_length=50, verbose_name='Domain')),
                ('subdomain_lang', models.BooleanField(default=False, verbose_name='Language subdomain')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='wikipage',
            name='project',
            field=models.ForeignKey(to='wikimedia.Wikiproject'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='wikipage',
            unique_together=set([('object_id', 'content_type', 'lang', 'project', 'title')]),
        ),
    ]
