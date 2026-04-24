from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackas', '0010_alter_aiusagelog_total_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackrequest',
            name='is_self_initiated',
            field=models.BooleanField(default=False, help_text='True jei atsiliepimas inicijuotas paties vertintojo, o ne paprašytas'),
        ),
    ]
