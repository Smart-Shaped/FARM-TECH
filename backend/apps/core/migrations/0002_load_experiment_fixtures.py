from django.db import migrations
from django.core.management import call_command

def load_fixtures(apps, schema_editor):
    call_command('loaddata', 'core_experiment_initial_data.json')
    
def reverse_load_fixtures(apps, schema_editor):
    experiment = apps.get_model('core', 'Experiment')
    experiment.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixtures, reverse_load_fixtures),
    ]
