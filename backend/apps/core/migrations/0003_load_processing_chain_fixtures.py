from django.db import migrations
from django.core.management import call_command
import os

def load_fixtures(apps, schema_editor):
    call_command('loaddata', 'core_processing_chain_initial_data.json')
    
def reverse_load_fixtures(apps, schema_editor):
    processing_chain = apps.get_model('core', 'ProcessingChain')
    processing_chain.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_load_experiment_fixtures'),
    ]

    operations = [
        migrations.RunPython(load_fixtures, reverse_load_fixtures),
    ]
