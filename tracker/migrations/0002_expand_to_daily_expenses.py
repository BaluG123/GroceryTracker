# Generated manually to preserve existing tracker data while broadening the domain.

from django.db import migrations, models
import django.db.models.deletion


def backfill_purchase_snapshots(apps, schema_editor):
    Purchase = apps.get_model('tracker', 'Purchase')
    for purchase in Purchase.objects.select_related('item').all():
        item = purchase.item
        if item:
            if not purchase.item_name_snapshot:
                purchase.item_name_snapshot = item.name
            if not purchase.unit_type_snapshot:
                purchase.unit_type_snapshot = item.unit_type
            if not purchase.category_snapshot:
                purchase.category_snapshot = item.category
            if not purchase.currency_code:
                purchase.currency_code = 'INR'
            purchase.save(update_fields=[
                'item_name_snapshot',
                'unit_type_snapshot',
                'category_snapshot',
                'currency_code',
            ])


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groceryitem',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='groceryitem',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='groceryitem',
            name='unit_type',
            field=models.CharField(default='unit', help_text='Flexible unit label, e.g., kg, litre, trip, month, meal, ticket.', max_length=30),
        ),
        migrations.AddField(
            model_name='purchase',
            name='category_snapshot',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='purchase',
            name='currency_code',
            field=models.CharField(default='INR', max_length=3),
        ),
        migrations.AddField(
            model_name='purchase',
            name='item_name_snapshot',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='purchase',
            name='location',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='purchase',
            name='merchant_name',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='purchase',
            name='unit_type_snapshot',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='tracker.groceryitem'),
        ),
        migrations.RunPython(backfill_purchase_snapshots, migrations.RunPython.noop),
    ]
