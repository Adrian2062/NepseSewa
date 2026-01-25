from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0025_add_recommendation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockrecommendation',
            name='rsi',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='expected_move',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='confidence',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
