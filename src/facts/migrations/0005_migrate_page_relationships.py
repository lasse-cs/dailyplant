from django.db import migrations


def copy_live_relationships(apps, schema_editor):
    FactPageRelatedFact = apps.get_model("facts", "FactPageRelatedFact")
    PageRelationship = apps.get_model("core", "PageRelationship")

    PageRelationship.objects.bulk_create(
        [
            PageRelationship(
                source_id=relationship.owner_id,
                target_id=relationship.fact_id,
            )
            for relationship in FactPageRelatedFact.objects.iterator()
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_pagerelationship"),
        ("facts", "0004_factpage_image_factpage_image_alt_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_live_relationships),
        migrations.DeleteModel(
            name="FactPageRelatedFact",
        ),
    ]
