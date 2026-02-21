from django.db import migrations, models
import django.db.models.deletion

def migrate_sectors(apps, schema_editor):
    Stock = apps.get_model('myapp', 'Stock')
    Sector = apps.get_model('myapp', 'Sector')
    
    # Get all unique sector names from current stocks
    sector_names = Stock.objects.values_list('sector_old', flat=True).distinct()
    
    for name in sector_names:
        if name:
            sector, _ = Sector.objects.get_or_create(name=name)
            # Update all stocks that had this sector name
            Stock.objects.filter(sector_old=name).update(sector=sector)
    
    # Default for empty sectors
    uncategorized, _ = Sector.objects.get_or_create(name="Uncategorized")
    Stock.objects.filter(sector__isnull=True).update(sector=uncategorized)

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0030_alter_stockrecommendation_options_and_more'),
    ]

    operations = [
        # 1. Create the Sector model
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'db_table': 'sectors',
                'verbose_name_plural': 'Sectors',
            },
        ),
        
        # 2. Rename existing sector CharField to sector_old
        migrations.RenameField(
            model_name='stock',
            old_name='sector',
            new_name='sector_old',
        ),
        
        # 3. Add the new sector ForeignKey field
        migrations.AddField(
            model_name='stock',
            name='sector',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stocks', to='myapp.sector'),
        ),
        
        # 4. Run data migration
        migrations.RunPython(migrate_sectors),
        
        # 5. Remove the old field
        migrations.RemoveField(
            model_name='stock',
            name='sector_old',
        ),
        
        # 6. Add the other new fields
        migrations.AddField(
            model_name='stock',
            name='change',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stock',
            name='last_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stock',
            name='volume',
            field=models.FloatField(blank=True, null=True),
        ),
        
        # 7. Add the new index
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['sector', 'symbol'], name='stocks_sector__38110f_idx'),
        ),
    ]
