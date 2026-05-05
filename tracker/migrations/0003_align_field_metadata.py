# Align model field metadata after the expense-tracker expansion.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_expand_to_daily_expenses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryitem',
            name='category',
            field=models.CharField(blank=True, default='', help_text='Optional spending category, e.g., Groceries, Transport, Bills, Health.', max_length=50),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='notes',
            field=models.TextField(blank=True, default='', help_text='Optional notes about the expense.'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='quantity',
            field=models.DecimalField(decimal_places=2, help_text='Number of units bought, e.g., 2 litres, 1 trip, 1 month.', max_digits=10),
        ),
    ]
