"""Custom Sentinel Objects

In some places of the user-facing API ``None`` is a meaningful value, e.g. for
``index=None``. However, we still want the plugin to decide the default value
for index. Hence, we introduce custom sentinel objects that allow plugins to
control the default behavior.

"""


class PluginDefaultSentinel:
    pass


PLUGIN_DEFAULT = PluginDefaultSentinel()
