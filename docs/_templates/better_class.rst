{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

    .. currentmodule:: {{ module }}


    .. rubric:: {{ _('Methods') }}

    .. autosummary::
    {% for item in methods %}
    {% if item != "__init__"%}
        ~{{ name }}.{{ item }}
    {% endif %}
    {%- endfor %}


    .. rubric:: Attribute and Method Details

    {% for item in attributes %}
    .. autoattribute::  {{ module }}.{{ name }}.{{ item }}
    {%- endfor %}   

    {% for item in methods %}
    {% if item != "__init__"%}
    .. automethod::  {{ module }}.{{ name }}.{{ item }}
    {% endif %}
    {%- endfor %}
