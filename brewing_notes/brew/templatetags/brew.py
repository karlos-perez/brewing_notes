import json

from urllib.parse import urlencode
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template import Library
from django.template.defaultfilters import floatformat

from brew.models import Recipe
from brew.utils import gravity_plato, get_i25_j25, srm_calc


register = Library()

@register.simple_tag
def setting(name):
    return getattr(settings, name, "")


@register.simple_tag
def is_debug():
    return settings.DEBUG


@register.simple_tag
def url_replace(request, field, value, direction=''):
    dict_ = request.GET.copy()
    if field == 'order_by' and field in dict_.keys():
        if dict_[field].startswith('-') and dict_[field].lstrip('-') == value:
            dict_[field] = value
        elif dict_[field].lstrip('-') == value:
            dict_[field] = "-" + value
        else:
            dict_[field] = direction + value
    else:
        dict_[field] = direction + value
    return urlencode(OrderedDict(sorted(dict_.items())))


@register.filter('formatted_float')
def formatted_float(value):
    value = floatformat(value, arg=3)
    return str(value).replace(',', '.')


@register.filter
def comma_to_dot(value):
    """
    in float
    out str
    34,5 -> 34.5
    """
    return str(value).replace(',', '.')


@register.filter
def gravity_to_plato(sg):
    """
    in: 1,033
    out: 1.033 (8.3 °P)
    """
    gravity = str(sg).replace(",", ".")
    if float(sg) > 1.000:
        plato = gravity_plato(float(sg))
        p = str(plato).replace(".", ",")
    else:
        p = 0
    return f'{gravity} ({p}\N{DEGREE SIGN}P)'

@register.filter
def pressure(psi):
    """
    in: 11
    out: 11psi (0.9 bar)
    """
    result = 0
    if psi:
        bar = round(float(psi) * 0.06894, 1)
        result = f'{psi}psi ({bar}bar)'
    return result


@register.filter
def gram_to_kg(g):
    """
    in: 500 gram
    out: 0.5 kg
    """
    return g / 1000


@register.filter
def verbose_name(obj):
    if obj:
        return obj._meta.verbose_name


@register.filter('columns')
def columns(thelist, n):
    """
    Break a list into ``n`` columns, filling up each column to the maximum equal
    length possible. (https://djangosnippets.org/snippets/401/)
    For example::

        >>> from pprint import pprint
        >>> for i in range(7, 11):
        ...     print '%sx%s:' % (i, 3)
        ...     pprint(columns(range(i), 3), width=20)
        7x3:
        [[0, 3, 6],
         [1, 4],
         [2, 5]]
        8x3:
        [[0, 3, 6],
         [1, 4, 7],
         [2, 5]]
        9x3:
        [[0, 3, 6],
         [1, 4, 7],
         [2, 5, 8]]
        10x3:
        [[0, 4, 8],
         [1, 5, 9],
         [2, 6],
         [3, 7]]

        # Note that this filter does not guarantee that `n` columns will be
        # present:
        >>> pprint(columns(range(4), 3), width=10)
        [[0, 2],
         [1, 3]]
    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    list_len = len(thelist)
    split = list_len // n
    if list_len % n != 0:
        split += 1
    return [thelist[i::split] for i in range(split)]


@register.filter()
def qs_distinct(qs, attr_name):
    """
    Remove duplicates from a QuerySet
    Use:
    {% for tag in post.mytags.all|qs_distinct:'user_agent' %}
    """
    return set([getattr(i, attr_name) for i in qs])


# @register.filter()
# def qs_distinct_sum(qs, attr_name):
#     """
#     Sum duplicates from a QuerySet
#     Use:
#     {% for tag in post.mytags.all|qs_distinct_sum:'amount' %}
#     """
#     new_qs = dict()
#     for i in qs:
#         if i in new_qs:
#             sum_attr = new_qs[i] + float(getattr(i, attr_name))
#             new_qs[i] = sum_attr
#         else:
#             new_qs[i] = getattr(i, attr_name)
#     return new_qs


@register.filter('proportion')
def proportion_grain(share, total):
    """
    Returns what percentage of the total
    Use:
    {% amount|proportion:total %}
    """
    return round((share/total)*100, 1)


@register.filter('recount')
def recalculate(amount, rc):
    if amount:
        return round(float(amount) * float(rc), 2)


@register.filter('i25')
def i25(index):
    result = {}
    try:
        recipe = Recipe.objects.get(id=index)
        result = json.dumps(get_i25_j25(recipe))
    except ObjectDoesNotExist:
        pass
    return result


@register.filter('srm')
def srm(index):
    result = 0
    try:
        recipe = Recipe.objects.get(id=index)
        grain = recipe.grainingredients_set.all()
        batch = float(recipe.batch_size)
        result = srm_calc(grain, [], batch)
    except ObjectDoesNotExist:
        pass
    return result
