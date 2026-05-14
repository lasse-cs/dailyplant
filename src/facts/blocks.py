from wagtail.blocks import RichTextBlock, StreamBlock, StructBlock, URLBlock


class ReferenceStructBlock(StructBlock):
    label = RichTextBlock(features=["bold", "italic"])
    url = URLBlock()

    class Meta:
        template = "patterns/components/facts/reference.html"


class ReferenceStreamBlock(StreamBlock):
    reference = ReferenceStructBlock()

    class Meta:
        block_counts = {"reference": {"min_num": 1}}
