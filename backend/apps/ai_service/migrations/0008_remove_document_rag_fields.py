from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_service", "0007_add_document_user_field"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="document",
            name="embedding",
        ),
        migrations.RemoveField(
            model_name="document",
            name="chunk_index",
        ),
        migrations.RemoveField(
            model_name="document",
            name="parent_document",
        ),
    ]
