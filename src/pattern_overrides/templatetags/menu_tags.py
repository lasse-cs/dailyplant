from pattern_library.monkey_utils import override_tag

from core.templatetags.menu_tags import register


override_tag(register, name="main_menu")
