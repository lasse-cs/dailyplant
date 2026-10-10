from wagtail.blocks import StreamBlock

from core.blocks import ReferenceStructBlock


class ReferenceStreamBlock(StreamBlock):
    reference = ReferenceStructBlock()

    class Meta:
        block_counts = {"reference": {"min_num": 1}}
