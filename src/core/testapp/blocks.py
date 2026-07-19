from wagtail import blocks

from core.blocks import HeadingBlock


class NestedStreamBlock(blocks.StreamBlock):
    heading = HeadingBlock()


class GroupedContentBlock(blocks.StructBlock):
    introduction = HeadingBlock()
    items = blocks.ListBlock(HeadingBlock())
    body = NestedStreamBlock()


class RootStreamBlock(blocks.StreamBlock):
    group = GroupedContentBlock()
    paragraph = blocks.CharBlock()
