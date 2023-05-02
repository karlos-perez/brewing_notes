import logging

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from nnmware.core.ajax import ajax_answer_lazy
from nnmware.core.exceptions import AccessError

from brew.constants import GRAM, MEASURE
from brew.models import Recipe

from catalog.models import Malt, Hops, Yeasts, Fermentable, Misc

from .models import Pantry, MaltsReserve, MaltsWriteOff, HopsReserve, YeastsReserve, HopsWriteOff, YeastsWriteOff, \
                    FermentableReserve, MiscReserve, FermentableWriteOff, MiscWriteOff

logger = logging.getLogger(__name__)


def pantry_parish_malt_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            malt_id = request.POST.get('malts', None)
            if malt_id is not None:
                malt = Malt.objects.get(pk=int(malt_id))
                malt_reserve = MaltsReserve()
                malt_reserve.pantry = pantry
                malt_reserve.malt = malt
                malt_reserve.parish = request.POST.get('malt_parish', 0)
                malt_reserve.balance = request.POST.get('malt_parish', 0)
                malt_reserve.cost_per_unit = request.POST.get('malt_cost_per_unit', 0)
                malt_reserve.supplier = request.POST.get('malt_supplier', '')
                malt_reserve.note = request.POST.get('malt_note', '')
                dt = request.POST.get('malt_date', '')
                if dt:
                    date = datetime.strptime(dt, "%d.%m.%Y").date()
                else:
                    date = None
                malt_reserve.created_date = date
                malt_reserve.save()
                payload = {'success': True,
                           'id': malt_reserve.id,
                           'malt': f'{malt_reserve.malt.name}',
                           'parish': malt_reserve.parish,
                           'cost': malt_reserve.cost_per_unit,
                           'date': dt,
                           'supplier': malt_reserve.supplier}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add malt')}
        logger.error(f'Ajax add malt in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find malt')}
    except Exception as err:
        logger.error(f'Ajax add malt in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add malt in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_malt_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        malt = get_object_or_404(MaltsReserve, pk=object_id)
        malt.delete()
        payload = {'success': True,
                   'id': f'malt-{object_id}'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete malt')}
        logger.error(f'Ajax delete malt in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete malt in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete malt in pantry')}
    return ajax_answer_lazy(payload)


def pantry_consumption_malt_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            recipe_id = request.POST.get('recipe', None)
            if recipe_id:
                recipe = Recipe.objects.get(id=int(recipe_id))
            else:
                recipe = None
            malt_reserve_id = request.POST.get('malts_reserve', None)
            if malt_reserve_id is not None:
                malt_reserve = MaltsReserve.objects.get(pk=int(malt_reserve_id))
                amount = float(request.POST.get('malt_amount', 0))
                balance = float(malt_reserve.balance)
                if amount <= balance:
                    malt_consumption = MaltsWriteOff()
                    malt_consumption.pantry = pantry
                    malt_consumption.recipe = recipe
                    malt_consumption.malt_reserve = malt_reserve
                    malt_consumption.amount = amount
                    malt_consumption.cost = round(float(malt_reserve.cost_per_unit) * amount, 2)
                    malt_consumption.note = request.POST.get('malt_note', '')
                    dt = request.POST.get('malt_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    malt_consumption.date = date
                    malt_consumption.save()
                    new_balance = balance - amount
                    malt_reserve.balance = new_balance
                    if new_balance == 0:
                        malt_reserve.spent = True
                    malt_reserve.save()
                    if recipe:
                        recipe_name = recipe.name
                    else:
                        recipe_name = None
                    payload = {'success': True,
                               'recipe': recipe_name,
                               'malt': malt_reserve.malt.name,
                               'amount': amount,
                               'cost': malt_consumption.cost,
                               'date': dt,
                               'mcID': malt_consumption.id}
                else:
                    payload = {'success': False, 'error': _('Malt consumption error. Consumption more parish'),
                               'balance': balance}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add consumption malt')}
        logger.error(f'Ajax add consumption malt in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find malt or recipe')}
    except Exception as err:
        logger.error(f'Ajax add consumption malt in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add consumption malt')}
    return ajax_answer_lazy(payload)


def pantry_consumption_malt_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        malt = get_object_or_404(MaltsWriteOff, pk=object_id)
        malt_reserve = malt.malt_reserve
        amount = float(malt_reserve.balance) + float(malt.amount)
        if amount <= float(malt_reserve.parish):
            malt_reserve.balance = amount
            malt_reserve.spent = False
            malt_reserve.save()
            malt.delete()
            payload = {'success': True,
                       'id': f'malt-{object_id}'}
        else:
            payload = {'success': False, 'error': _('The amount of malt write-offs more parish')}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete malt')}
        logger.error(f'Ajax delete malt in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete malt in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete malt in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_hop_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            hop_id = request.POST.get('hops', None)
            if hop_id is not None:
                hop = Hops.objects.get(pk=int(hop_id))
                hop_reserve = HopsReserve()
                hop_reserve.pantry = pantry
                hop_reserve.hop = hop
                hop_reserve.alfa = request.POST.get('hop_alfa', 0)
                hop_reserve.parish = request.POST.get('hop_parish', 0)
                hop_reserve.balance = request.POST.get('hop_parish', 0)
                hop_reserve.cost_per_unit = request.POST.get('hop_cost_per_unit', 0)
                hop_reserve.supplier = request.POST.get('hop_supplier', '')
                hop_reserve.note = request.POST.get('hop_note', '')
                dt = request.POST.get('hop_date', '')
                if dt:
                    date = datetime.strptime(dt, "%d.%m.%Y").date()
                else:
                    date = None
                hop_reserve.created_date = date
                hop_reserve.save()
                payload = {'success': True,
                           'id': hop_reserve.id,
                           'hop': f'{hop_reserve.hop.name}',
                           'alfa': hop_reserve.alfa,
                           'parish': hop_reserve.parish,
                           'cost': hop_reserve.cost_per_unit,
                           'date': dt,
                           'supplier': hop_reserve.supplier}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add hop')}
        logger.error(f'Ajax add hop in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find hop')}
    except Exception as err:
        logger.error(f'Ajax add hop in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add hop in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_hop_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        hop = get_object_or_404(HopsReserve, pk=object_id)
        hop.delete()
        payload = {'success': True,
                   'id': f'hop-{object_id}'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete hop')}
        logger.error(f'Ajax delete hop in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete hop in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete hop in pantry')}
    return ajax_answer_lazy(payload)


def pantry_consumption_hop_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            recipe_id = request.POST.get('recipe', None)
            if recipe_id:
                recipe = Recipe.objects.get(id=int(recipe_id))
            else:
                recipe = None
            hop_reserve_id = request.POST.get('hops_reserve', None)
            if hop_reserve_id is not None:
                hop_reserve = HopsReserve.objects.get(pk=int(hop_reserve_id))
                amount = float(request.POST.get('hop_amount', 0))
                balance = float(hop_reserve.balance)
                if amount <= balance:
                    hop_consumption = HopsWriteOff()
                    hop_consumption.pantry = pantry
                    hop_consumption.recipe = recipe
                    hop_consumption.hop_reserve = hop_reserve
                    hop_consumption.amount = amount
                    hop_consumption.cost = round(float(hop_reserve.cost_per_unit) * amount, 2)
                    hop_consumption.note = request.POST.get('hop_note', '')
                    dt = request.POST.get('hop_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    hop_consumption.date = date
                    hop_consumption.save()
                    new_balance = balance - amount
                    hop_reserve.balance = new_balance
                    if new_balance == 0:
                        hop_reserve.spent = True
                    hop_reserve.save()
                    if recipe:
                        recipe_name = recipe.name
                    else:
                        recipe_name = None
                    payload = {'success': True,
                               'recipe': recipe_name,
                               'hop': hop_reserve.hop.name,
                               'amount': amount,
                               'cost': hop_consumption.cost,
                               'date': dt,
                               'hcID': hop_consumption.id}
                else:
                    payload = {'success': False, 'error': _('Hop consumption error. Consumption more parish'),
                               'balance': balance}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add consumption hop')}
        logger.error(f'Ajax add consumption hop in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find hop or recipe')}
    except Exception as err:
        logger.error(f'Ajax add consumption hop in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _(f'Error add consumption hop')}
    return ajax_answer_lazy(payload)


def pantry_consumption_hop_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        hop = get_object_or_404(HopsWriteOff, pk=object_id)
        hop_reserve = hop.hop_reserve
        amount = float(hop_reserve.balance) + float(hop.amount)
        if amount <= float(hop_reserve.parish):
            hop_reserve.balance = amount
            hop_reserve.spent = False
            hop_reserve.save()
            hop.delete()
            payload = {'success': True,
                       'id': f'hop-{object_id}'}
        else:
            payload = {'success': False, 'error': _('The amount of hop write-offs more parish')}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete hop')}
        logger.error(f'Ajax delete hop in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete hop in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete hop in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_yeast_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            yeast_id = request.POST.get('yeasts', None)
            if yeast_id is not None:
                yeast = Yeasts.objects.get(pk=int(yeast_id))
                yeast_reserve = YeastsReserve()
                yeast_reserve.pantry = pantry
                yeast_reserve.yeast = yeast
                yeast_reserve.measure = request.POST.get('yeast_measure', GRAM)
                yeast_reserve.parish = request.POST.get('yeast_parish', 0)
                yeast_reserve.balance = request.POST.get('yeast_parish', 0)
                yeast_reserve.cost_per_unit = request.POST.get('yeast_cost_per_unit', 0)
                yeast_reserve.supplier = request.POST.get('yeast_supplier', '')
                yeast_reserve.note = request.POST.get('yeast_note', '')
                created_date = request.POST.get('yeast_cr_date', '')
                if created_date:
                    cr_date = datetime.strptime(created_date, "%d.%m.%Y").date()
                else:
                    cr_date = None
                yeast_reserve.created_date = cr_date
                expiration_date = request.POST.get('yeast_ex_date', '')
                if expiration_date:
                    ex_date = datetime.strptime(expiration_date, "%d.%m.%Y").date()
                else:
                    ex_date = None
                yeast_reserve.expiration_date = ex_date
                yeast_reserve.save()
                payload = {'success': True,
                           'id': yeast_reserve.id,
                           'yeast': f'{yeast_reserve.yeast.name}',
                           'parish': f'{yeast_reserve.parish} {MEASURE[int(yeast_reserve.measure)][1]}',
                           'cost': yeast_reserve.cost_per_unit,
                           'crDate': created_date,
                           'exDate': expiration_date,
                           'supplier': yeast_reserve.supplier}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add yeast')}
        logger.error(f'Ajax add yeast in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find yeast')}
    except Exception as err:
        logger.error(f'Ajax add yeast in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add yeast in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_yeast_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        yeast = get_object_or_404(YeastsReserve, pk=object_id)
        yeast.delete()
        payload = {'success': True,
                   'id': f'yeast-{object_id}'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete yeast')}
        logger.error(f'Ajax delete yeast in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete yeast in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete yeast in pantry')}
    return ajax_answer_lazy(payload)


def pantry_consumption_yeast_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            recipe_id = request.POST.get('recipe', None)
            if recipe_id:
                recipe = Recipe.objects.get(id=int(recipe_id))
            else:
                recipe = None
            yeast_reserve_id = request.POST.get('yeasts_reserve', None)
            if yeast_reserve_id is not None:
                yeast_reserve = YeastsReserve.objects.get(pk=int(yeast_reserve_id))
                amount = float(request.POST.get('yeast_amount', 0))
                balance = float(yeast_reserve.balance)
                if amount <= balance:
                    yeast_consumption = YeastsWriteOff()
                    yeast_consumption.pantry = pantry
                    yeast_consumption.recipe = recipe
                    yeast_consumption.yeast_reserve = yeast_reserve
                    yeast_consumption.amount = amount
                    yeast_consumption.measure = yeast_reserve.measure
                    yeast_consumption.cost = round(float(yeast_reserve.cost_per_unit) * amount, 2)
                    yeast_consumption.note = request.POST.get('yeast_note', '')
                    dt = request.POST.get('yeast_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    yeast_consumption.date = date
                    yeast_consumption.save()
                    new_balance = balance - amount
                    yeast_reserve.balance = new_balance
                    if new_balance == 0:
                        yeast_reserve.spent = True
                    yeast_reserve.save()
                    if recipe:
                        recipe_name = recipe.name
                    else:
                        recipe_name = None
                    payload = {'success': True,
                               'recipe': recipe_name,
                               'yeast': yeast_reserve.yeast.name,
                               'amount': f'{amount} {MEASURE[yeast_consumption.measure][1]}',
                               'cost': yeast_consumption.cost,
                               'date': dt,
                               'ycID': yeast_consumption.id}
                else:
                    payload = {'success': False, 'error': _('Yeast consumption error. Consumption more parish'),
                               'balance': balance}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add consumption yeast')}
        logger.error(f'Ajax add consumption yeast in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find yeast or recipe')}
    except Exception as err:
        logger.error(f'Ajax add consumption yeast in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _(f'Error add consumption yeast')}
    return ajax_answer_lazy(payload)


def pantry_consumption_yeast_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        yeast = get_object_or_404(YeastsWriteOff, pk=object_id)
        yeast_reserve = yeast.yeast_reserve
        amount = float(yeast_reserve.balance) + float(yeast.amount)
        if amount <= float(yeast_reserve.parish):
            yeast_reserve.balance = amount
            yeast_reserve.spent = False
            yeast_reserve.save()
            yeast.delete()
            payload = {'success': True,
                       'id': f'yeast-{object_id}'}
        else:
            payload = {'success': False, 'error': _('The amount of yeast write-offs more parish')}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete yeast')}
        logger.error(f'Ajax delete yeast in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete yeast in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete yeast in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_fermentable_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            fermentable_id = request.POST.get('fermentable', None)
            if fermentable_id is not None:
                fermentable = Fermentable.objects.get(pk=int(fermentable_id))
                fermentable_reserve = FermentableReserve()
                fermentable_reserve.pantry = pantry
                fermentable_reserve.fermentable = fermentable
                fermentable_reserve.measure = request.POST.get('fermentable_measure', GRAM)
                fermentable_reserve.parish = request.POST.get('fermentable_parish', 0)
                fermentable_reserve.balance = request.POST.get('fermentable_parish', 0)
                fermentable_reserve.cost_per_unit = request.POST.get('fermentable_cost_per_unit', 0)
                fermentable_reserve.supplier = request.POST.get('fermentable_supplier', '')
                fermentable_reserve.note = request.POST.get('fermentable_note', '')
                created_date = request.POST.get('fermentable_cr_date', '')
                if created_date:
                    cr_date = datetime.strptime(created_date, "%d.%m.%Y").date()
                else:
                    cr_date = None
                fermentable_reserve.created_date = cr_date
                # expiration_date = request.POST.get('fermentable_ex_date', '')
                # if expiration_date:
                #     ex_date = datetime.strptime(expiration_date, "%d.%m.%Y").date()
                # else:
                #     ex_date = None
                # fermentable_reserve.expiration_date = ex_date
                fermentable_reserve.save()
                payload = {'success': True,
                           'id': fermentable_reserve.id,
                           'fermentable': f'{fermentable_reserve.fermentable.name}',
                           'parish': f'{fermentable_reserve.parish} {MEASURE[int(fermentable_reserve.measure)][1]}',
                           'cost': fermentable_reserve.cost_per_unit,
                           'crDate': created_date,
                           # 'exDate': expiration_date,
                           'supplier': fermentable_reserve.supplier}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add fermentable')}
        logger.error(f'Ajax add fermentable in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find fermentable')}
    except Exception as err:
        logger.error(f'Ajax add fermentable in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add fermentable in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_fermentable_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        fermentable = get_object_or_404(FermentableReserve, pk=object_id)
        fermentable.delete()
        payload = {'success': True,
                   'id': f'fermentable-{object_id}'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete fermentable')}
        logger.error(f'Ajax delete fermentable in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete fermentable in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete fermentable in pantry')}
    return ajax_answer_lazy(payload)


def pantry_consumption_fermentable_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            recipe_id = request.POST.get('recipe', None)
            if recipe_id:
                recipe = Recipe.objects.get(id=int(recipe_id))
            else:
                recipe = None
            fermentable_reserve_id = request.POST.get('fermentable_reserve', None)
            if fermentable_reserve_id is not None:
                fermentable_reserve = FermentableReserve.objects.get(pk=int(fermentable_reserve_id))
                amount = float(request.POST.get('fermentable_amount', 0))
                balance = float(fermentable_reserve.balance)
                if amount <= balance:
                    fermentable_consumption = FermentableWriteOff()
                    fermentable_consumption.pantry = pantry
                    fermentable_consumption.recipe = recipe
                    fermentable_consumption.fermentable_reserve = fermentable_reserve
                    fermentable_consumption.amount = amount
                    fermentable_consumption.measure = fermentable_reserve.measure
                    fermentable_consumption.cost = round(float(fermentable_reserve.cost_per_unit) * amount, 2)
                    fermentable_consumption.note = request.POST.get('fermentable_note', '')
                    dt = request.POST.get('fermentable_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    fermentable_consumption.date = date
                    fermentable_consumption.save()
                    new_balance = balance - amount
                    fermentable_reserve.balance = new_balance
                    if new_balance == 0:
                        fermentable_reserve.spent = True
                    fermentable_reserve.save()
                    if recipe:
                        recipe_name = recipe.name
                    else:
                        recipe_name = None
                    payload = {'success': True,
                               'recipe': recipe_name,
                               'fermentable': fermentable_reserve.fermentable.name,
                               'amount': f'{amount} {MEASURE[fermentable_consumption.measure][1]}',
                               'cost': fermentable_consumption.cost,
                               'date': dt,
                               'fcID': fermentable_consumption.id}
                else:
                    payload = {'success': False, 'error': _('Fermentable consumption error. Consumption more parish'),
                               'balance': balance}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add consumption fermentable')}
        logger.error(f'Ajax add consumption fermentable in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find fermentable or recipe')}
    except Exception as err:
        logger.error(f'Ajax add consumption fermentable in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _(f'Error add consumption fermentable')}
    return ajax_answer_lazy(payload)


def pantry_consumption_fermentable_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        fermentable = get_object_or_404(FermentableWriteOff, pk=object_id)
        fermentable_reserve = fermentable.fermentable_reserve
        amount = float(fermentable_reserve.balance) + float(fermentable.amount)
        if amount <= float(fermentable_reserve.parish):
            fermentable_reserve.balance = amount
            fermentable_reserve.spent = False
            fermentable_reserve.save()
            fermentable.delete()
            payload = {'success': True,
                       'id': f'fermentable-{object_id}'}
        else:
            payload = {'success': False, 'error': _('The amount of fermentable write-offs more parish')}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete fermentable')}
        logger.error(f'Ajax delete fermentable in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete fermentable in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete fermentable in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_misc_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            misc_id = request.POST.get('misc', None)
            if misc_id is not None:
                misc = Misc.objects.get(pk=int(misc_id))
                misc_reserve = MiscReserve()
                misc_reserve.pantry = pantry
                misc_reserve.misc = misc
                misc_reserve.measure = request.POST.get('misc_measure', GRAM)
                misc_reserve.parish = request.POST.get('misc_parish', 0)
                misc_reserve.balance = request.POST.get('misc_parish', 0)
                misc_reserve.cost_per_unit = request.POST.get('misc_cost_per_unit', 0)
                misc_reserve.supplier = request.POST.get('misc_supplier', '')
                misc_reserve.note = request.POST.get('misc_note', '')
                created_date = request.POST.get('misc_cr_date', '')
                if created_date:
                    cr_date = datetime.strptime(created_date, "%d.%m.%Y").date()
                else:
                    cr_date = None
                misc_reserve.created_date = cr_date
                # expiration_date = request.POST.get('misc_ex_date', '')
                # if expiration_date:
                #     ex_date = datetime.strptime(expiration_date, "%d.%m.%Y").date()
                # else:
                #     ex_date = None
                # misc_reserve.expiration_date = ex_date
                misc_reserve.save()
                payload = {'success': True,
                           'id': misc_reserve.id,
                           'misc': f'{misc_reserve.misc.name}',
                           'parish': f'{misc_reserve.parish} {MEASURE[int(misc_reserve.measure)][1]}',
                           'cost': misc_reserve.cost_per_unit,
                           'crDate': created_date,
                           # 'exDate': expiration_date,
                           'supplier': misc_reserve.supplier}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add misc')}
        logger.error(f'Ajax add misc in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find misc')}
    except Exception as err:
        logger.error(f'Ajax add misc in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error add misc in pantry')}
    return ajax_answer_lazy(payload)


def pantry_parish_misc_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        misc = get_object_or_404(MiscReserve, pk=object_id)
        misc.delete()
        payload = {'success': True,
                   'id': f'misc-{object_id}'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete misc')}
        logger.error(f'Ajax delete misc in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete misc in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete misc in pantry')}
    return ajax_answer_lazy(payload)


def pantry_consumption_misc_add(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        pantry = get_object_or_404(Pantry, pk=object_id)
        if pantry.user == request.user or request.user.is_superuser:
            recipe_id = request.POST.get('recipe', None)
            if recipe_id:
                recipe = Recipe.objects.get(id=int(recipe_id))
            else:
                recipe = None
            misc_reserve_id = request.POST.get('misc_reserve', None)
            if misc_reserve_id is not None:
                misc_reserve = MiscReserve.objects.get(pk=int(misc_reserve_id))
                amount = float(request.POST.get('misc_amount', 0))
                balance = float(misc_reserve.balance)
                if amount <= balance:
                    misc_consumption = MiscWriteOff()
                    misc_consumption.pantry = pantry
                    misc_consumption.recipe = recipe
                    misc_consumption.misc_reserve = misc_reserve
                    misc_consumption.amount = amount
                    misc_consumption.measure = misc_reserve.measure
                    misc_consumption.cost = round(float(misc_reserve.cost_per_unit) * amount, 2)
                    misc_consumption.note = request.POST.get('misc_note', '')
                    dt = request.POST.get('misc_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    misc_consumption.date = date
                    misc_consumption.save()
                    new_balance = balance - amount
                    misc_reserve.balance = new_balance
                    if new_balance == 0:
                        misc_reserve.spent = True
                    misc_reserve.save()
                    if recipe:
                        recipe_name = recipe.name
                    else:
                        recipe_name = None
                    payload = {'success': True,
                               'recipe': recipe_name,
                               'misc': misc_reserve.misc.name,
                               'amount': f'{amount} {MEASURE[misc_consumption.measure][1]}',
                               'cost': misc_consumption.cost,
                               'date': dt,
                               'mcID': misc_consumption.id}
                else:
                    payload = {'success': False, 'error': _('Misc consumption error. Consumption more parish'),
                               'balance': balance}
            else:
                raise ObjectDoesNotExist
    except AccessError:
        payload = {'success': False, 'error': _('You cannot add consumption misc')}
        logger.error(f'Ajax add consumption misc in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except ObjectDoesNotExist:
        payload = {'success': False, 'error': _('Can\'t find misc or recipe')}
    except Exception as err:
        logger.error(f'Ajax add consumption misc in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _(f'Error add consumption misc')}
    return ajax_answer_lazy(payload)


def pantry_consumption_misc_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        misc = get_object_or_404(MiscWriteOff, pk=object_id)
        misc_reserve = misc.misc_reserve
        amount = float(misc_reserve.balance) + float(misc.amount)
        if amount <= float(misc_reserve.parish):
            misc_reserve.balance = amount
            misc_reserve.spent = False
            misc_reserve.save()
            misc.delete()
            payload = {'success': True,
                       'id': f'misc-{object_id}'}
        else:
            payload = {'success': False, 'error': _('The amount of misc write-offs more parish')}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete misc')}
        logger.error(f'Ajax delete misc in pantry AccessError: '
                     f'user: {request.user.username}, '
                     f'pantry: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete misc in pantry: {err}, user: {request.user.username}, pantry: {object_id}')
        payload = {'success': False, 'error': _('Error delete misc in pantry')}
    return ajax_answer_lazy(payload)
