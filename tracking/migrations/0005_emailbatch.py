# Generated by Django 5.0.6 on 2024-06-23 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0004_unsubscribeduser"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailBatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("batch_size", models.IntegerField()),
                ("delay_between_emails", models.IntegerField()),
                ("delay_between_batches", models.IntegerField()),
                (
                    "schedule_type",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        max_length=50,
                    ),
                ),
                ("send_time", models.TimeField()),
                ("day_of_week", models.CharField(blank=True, max_length=10, null=True)),
                ("day_of_month", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("emails", models.ManyToManyField(to="tracking.email")),
            ],
        ),
    ]
