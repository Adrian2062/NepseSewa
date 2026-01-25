from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0024_subscriptionplan_tier'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockrecommendation',
            name='predicted_return',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='trend',
            field=models.CharField(choices=[('Bullish', 'Bullish'), ('Bearish', 'Bearish'), ('Neutral', 'Neutral')], default='Neutral', max_length=20),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='entry_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='target_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='stop_loss',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stockrecommendation',
            name='exit_price',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
