from django.db import migrations
from django.utils.text import slugify


def copy_live_tags(apps, schema_editor):
    FactTag = apps.get_model("facts", "FactTag")
    TaggedFact = apps.get_model("facts", "TaggedFact")
    Tag = apps.get_model("core", "Tag")
    PageTag = apps.get_model("core", "PageTag")

    tag_ids = {}
    for old_tag in FactTag.objects.iterator():
        base_slug = slugify(old_tag.name)[:100]
        if not base_slug:
            raise RuntimeError(f"Cannot create an ASCII slug for tag {old_tag.name!r}.")

        slug = base_slug
        index = 1
        while Tag.objects.filter(slug=slug).exists():
            index += 1
            suffix = f"-{index}"
            slug = f"{base_slug[: 100 - len(suffix)]}{suffix}"

        tag = Tag.objects.create(name=old_tag.name, slug=slug)
        tag_ids[old_tag.pk] = tag.pk

    assignments = {
        (assignment.content_object_id, tag_ids[assignment.tag_id])
        for assignment in TaggedFact.objects.iterator()
    }
    PageTag.objects.bulk_create(
        [PageTag(page_id=page_id, tag_id=tag_id) for page_id, tag_id in assignments]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_tag_pagetag"),
        ("facts", "0005_migrate_page_relationships"),
    ]

    operations = [
        migrations.RunPython(copy_live_tags),
        migrations.RemoveField(
            model_name="taggedfact",
            name="tag",
        ),
        migrations.RemoveField(
            model_name="factpage",
            name="tags",
        ),
        migrations.RemoveField(
            model_name="taggedfact",
            name="content_object",
        ),
        migrations.DeleteModel(
            name="FactTag",
        ),
        migrations.DeleteModel(
            name="TaggedFact",
        ),
    ]
