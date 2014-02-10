# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Building'
        db.create_table(u'FingerprintsREST_building', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('FingerprintsREST', ['Building'])

        # Adding model 'Device'
        db.create_table(u'FingerprintsREST_device', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, db_index=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
        ))
        db.send_create_signal('FingerprintsREST', ['Device'])

        # Adding model 'Location'
        db.create_table(u'FingerprintsREST_location', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('room', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['FingerprintsREST.Building'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('FingerprintsREST', ['Location'])

        # Adding unique constraint on 'Location', fields ['name', 'building']
        db.create_unique(u'FingerprintsREST_location', ['name', 'building_id'])

        # Adding model 'BaseStation'
        db.create_table(u'FingerprintsREST_basestation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bssid', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('ssid', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('frequency', self.gf('django.db.models.fields.IntegerField')()),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('FingerprintsREST', ['BaseStation'])

        # Adding unique constraint on 'BaseStation', fields ['bssid', 'frequency']
        db.create_unique(u'FingerprintsREST_basestation', ['bssid', 'frequency'])

        # Adding model 'Fingerprint'
        db.create_table(u'FingerprintsREST_fingerprint', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['FingerprintsREST.Location'], blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['FingerprintsREST.Device'], blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('direction', self.gf('django.db.models.fields.FloatField')()),
            ('magnitude', self.gf('django.db.models.fields.FloatField')()),
            ('zaxis', self.gf('django.db.models.fields.FloatField')()),
            ('confirmed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('FingerprintsREST', ['Fingerprint'])

        # Adding model 'Scan'
        db.create_table(u'FingerprintsREST_scan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('level', self.gf('django.db.models.fields.IntegerField')()),
            ('base_station', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['FingerprintsREST.BaseStation'])),
            ('fingerprint', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scans', to=orm['FingerprintsREST.Fingerprint'])),
        ))
        db.send_create_signal('FingerprintsREST', ['Scan'])


    def backwards(self, orm):
        # Removing unique constraint on 'BaseStation', fields ['bssid', 'frequency']
        db.delete_unique(u'FingerprintsREST_basestation', ['bssid', 'frequency'])

        # Removing unique constraint on 'Location', fields ['name', 'building']
        db.delete_unique(u'FingerprintsREST_location', ['name', 'building_id'])

        # Deleting model 'Building'
        db.delete_table(u'FingerprintsREST_building')

        # Deleting model 'Device'
        db.delete_table(u'FingerprintsREST_device')

        # Deleting model 'Location'
        db.delete_table(u'FingerprintsREST_location')

        # Deleting model 'BaseStation'
        db.delete_table(u'FingerprintsREST_basestation')

        # Deleting model 'Fingerprint'
        db.delete_table(u'FingerprintsREST_fingerprint')

        # Deleting model 'Scan'
        db.delete_table(u'FingerprintsREST_scan')


    models = {
        'FingerprintsREST.basestation': {
            'Meta': {'unique_together': "(('bssid', 'frequency'),)", 'object_name': 'BaseStation'},
            'bssid': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'ssid': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'FingerprintsREST.building': {
            'Meta': {'object_name': 'Building'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'FingerprintsREST.device': {
            'Meta': {'object_name': 'Device'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        },
        'FingerprintsREST.fingerprint': {
            'Meta': {'object_name': 'Fingerprint'},
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['FingerprintsREST.Device']", 'blank': 'True'}),
            'direction': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['FingerprintsREST.Location']", 'blank': 'True'}),
            'magnitude': ('django.db.models.fields.FloatField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'zaxis': ('django.db.models.fields.FloatField', [], {})
        },
        'FingerprintsREST.location': {
            'Meta': {'unique_together': "(('name', 'building'),)", 'object_name': 'Location'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['FingerprintsREST.Building']"}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'room': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'})
        },
        'FingerprintsREST.scan': {
            'Meta': {'object_name': 'Scan'},
            'base_station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['FingerprintsREST.BaseStation']"}),
            'fingerprint': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scans'", 'to': "orm['FingerprintsREST.Fingerprint']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['FingerprintsREST']