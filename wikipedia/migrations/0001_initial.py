# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WikipediaElement'
        db.create_table('wikipedia_wikipediaelement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('wikipedia', ['WikipediaElement'])

        # Adding unique constraint on 'WikipediaElement', fields ['object_id', 'content_type', 'lang', 'title']
        db.create_unique('wikipedia_wikipediaelement', ['object_id', 'content_type_id', 'lang', 'title'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'WikipediaElement', fields ['object_id', 'content_type', 'lang', 'title']
        db.delete_unique('wikipedia_wikipediaelement', ['object_id', 'content_type_id', 'lang', 'title'])

        # Deleting model 'WikipediaElement'
        db.delete_table('wikipedia_wikipediaelement')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wikipedia.wikipediaelement': {
            'Meta': {'ordering': "('-updated',)", 'unique_together': "(('object_id', 'content_type', 'lang', 'title'),)", 'object_name': 'WikipediaElement'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['wikipedia']
