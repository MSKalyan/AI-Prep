from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0006_remove_document_author_document_file_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="user",
            field=models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name="documents",
                db_index=True,
                null=True,
                blank=True,
            ),
        ),
    ]
