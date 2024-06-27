# Generated by Django 4.1.13 on 2024-06-26 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0008_alter_emailbatch_send_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailbatch",
            name="batch_size",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="body",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="delay_between_batches",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="delay_between_emails",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="recipients",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="schedule_type",
            field=models.CharField(
                choices=[
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("monthly", "Monthly"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="subject",
            field=models.CharField(max_length=200),
        ),
    ]