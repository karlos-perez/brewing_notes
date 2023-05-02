import logging
import math
import random
import secrets

from lxml import etree
from lxml.builder import E
from short_url import UrlEncoder

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum

from transliterate import translit

from catalog.constants import SUGAR, EXTRACT, PELLETS, ALE, LAGERS, WHEAT, \
                              SPICE, WATER_AGENT, HERBS, FINING, FLAVOR

from .constants import USE_BOIL, USE_HOP_STAND, USE_PRIMARY, USE_MASH, USE_BOTTLING, USE_SECONDARY,\
                       GRAM, KILOGRAM

# from .models import Recipe

logger = logging.getLogger(__name__)


DEFAULT_ALPHABET = 'vW8RSHyYmQD3wATrafUCdK9sNVqhk6Btun5c7G2M4gbzFJZEXPxpej'
DEFAULT_BLOCK_SIZE = 24
MIN_LENGTH = 5
TYPE_BEER = ('Light lager', 'Pilsner', 'Amber lager', 'Dark lager', 'Bock', 'IPA', 'Light ale', 'Amber Ale',
             'Brown Ale', 'Strong Ale', 'Sour Ale', 'Porter', 'Stout', 'Wheat beer', 'Special beer')
TYPE_REST = ('Mash in', 'Acid rest', 'Beta-glucanase rest', 'Protein rest', 'Maltose rest', 'Saccharification rest',
             'Dextrin rest', 'Mash out')
TYPE_HEATING = ('Infusion', 'Decoction', 'Temperature')


def get_uid(n: int) -> str:
    """
    Сonverts int -> str (12 -> mjy7y) for short url
    """
    ue = UrlEncoder(alphabet=DEFAULT_ALPHABET, block_size=DEFAULT_BLOCK_SIZE)
    x = n + random.randint(0, 999999)
    return ue.encode_url(x, min_length=MIN_LENGTH)

def get_token() -> str:
    """
    Return token for Devices
    """
    t = secrets.token_urlsafe().replace('-', '')
    t = t.replace('_', '')
    return t[:20]


def gravity_plato(sg: float) -> float:
    """
    Сonverts Gravity to Plato:
    in: 1.034 -> return: 8.5
    """
    sg = float(sg)
    plato = (-1 * 616.868) + (1111.14 * sg) - (630.272 * sg**2) + (135.997 * sg**3)
    return round(plato, 1)


def plato_gravity(plato: float) -> float:
    """
    Сonverts Plato to Gravity:
    in: 8.5 -> return: 1.034
    """
    plato = float(plato)
    gravity = (plato / (258.6 - ((plato / 258.2) * 227.1))) + 1
    return round(gravity, 3)


def ebc_srm(ebc: float) -> float:
    """
    Сonverts Color EBC to SRM:
    """
    return round(ebc / 1.97, 1)


def srm_ebc(srm: float) -> float:
    """
    Сonverts Color EBC to SRM:
    """
    return round(1.97 * srm, 1)


def alco_old(og, fg) -> float:
    """
    Alcohol By Volume ABV Calculator old formula
    og 1.045, fg 1.011 -> abv 4,5 %
    """
    og = float(og)
    fg = float(fg)
    abv = (og - fg) * 131.25
    return round(abv, 1)


def alco_new(og, fg) -> float:
    """
    Alcohol By Volume ABV Calculator new formula
    og 1.045, fg 1.011 -> abv 4.5 %
    """
    og = float(og)
    fg = float(fg)
    abv = ((76.08 * (og - fg)) / (1.775 - og)) * (fg / 0.794)
    return round(abv, 1)


def attenuation(og, fg) -> float:
    """
    Apparent Attenuation
    og 1.045, fg 1.011 -> 75 %
    """
    if float(og) > 1.000 and float(fg) >= 1.000:
        attn = (1 - (gravity_plato(fg) / gravity_plato(og))) * 100
    else:
        attn = 0
    return round(attn, 0)


def calories(og, fg) -> float:
    """
    Calories per 100g
    og 1.045, fg 1.011 -> 87.7 kCal
    """
    op = gravity_plato(og)
    fp = gravity_plato(fg)
    fg = float(fg)
    real_extract = (0.1808 * op) + (0.8192 * fp)
    abw = (op - real_extract) / (2.0665 - (0.010665 * op))
    calories = ((6.9 * abw) + 4.0 * (real_extract - 0.1)) * fg
    return round(calories, 0)


def alco_calc(og, fg) -> dict:
    """
    Alcohol Calculator
    og 1.045, fg 1.011 -> {abv:4.5, attenuation:75, calories:87}
    """
    og = float(og)
    fg = float(fg)
    result = {
        'abv': alco_new(og, fg),
        'attenuation': attenuation(og, fg),
        'calories': calories(og, fg),
    }
    return result

def alco(og, fg) -> dict:
    """
    Alcohol Calculator
    og 1.045, fg 1.011 -> 4.5 (4.7)%
    """
    og = float(og)
    fg = float(fg)
    return f'{alco_old(og, fg)} ({alco_new(og, fg)}) %'

def dry_extract_recipe(grains) -> float:
    """
    Calculate dry extract
    in Queryset: Recipe.grainingredients_set.all()
    return: total dry extract
    """
    total_dry_extract = float()
    for i in grains:
        dry_extract = (i.ingredient.extractivity * i.amount) / 100
        total_dry_extract += float(dry_extract)
    return total_dry_extract

def srm_calc(grain, ferms, batch_size) -> float:
    """
    Calculate Color SRM
    in Querysets: Recipe.grainingredients_set.all()
                  Recipe.fermentableingredients_set.all()

    return: color in SRM
    """
    batch_size = 0.264172052 * float(batch_size)

    mcu = float()
    for i in grain:
        m = 2.20462262 * float(i.ingredient.color) * (float(i.amount) / batch_size)
        mcu += m
    for i in ferms:
        m = 2.20462262 * float(i.ingredient.color) * (float(i.amount) / batch_size)
        mcu += m
    srm = round(1.4922 * (mcu**0.6859), 1)
    if srm >= 40:
        srm = 40
    return srm


def gravity_after_boil(pre_boil_size, batch_size, og) -> float:
    """
    Calculate pre boil gravity
    return: PBG
    """
    pre_boil_size = float(pre_boil_size)
    batch_size = float(batch_size)
    og = float(og)
    calc_pbg = batch_size / pre_boil_size * (og - 1) + 1
    return calc_pbg


def calc_pre_boil_size(mash_water, sparge_water, total_grain, residue=0.5):
    """
    Calculate value wort on boil
    """
    return float(mash_water + sparge_water) - residue - (total_grain * 1.04)


def ibu_calc(recipe: object, total_grain: float) -> int:
    """
    Calculate Tinset IBU
    in Queryset: Recipe.hopsingredients_set.all()
    return: total IBU
    """
    hops = recipe.hopsingredients_set.filter(use=USE_BOIL)
    if recipe.pre_boil_size:
        boil_size = float(recipe.pre_boil_size)
    else:
        boil_size = calc_pre_boil_size(recipe.mash_water, recipe.sparge_water, total_grain)
    batch_size = float(recipe.batch_size)
    og = float(recipe.OG)
    if recipe.PBG:
        pbg = float(recipe.PBG)
    else:
        pbg = gravity_after_boil(boil_size, batch_size, og)
    total_ibu = 0
    for i in hops:
        weight = float(i.amount)
        alfa = float(i.alfa)
        time = i.time
        bfactor = 1.65 * 0.000125**(pbg - 1)
        tfactor = (1 - math.e**(-0.04 * time)) / 4.15
        util = bfactor * tfactor
        if i.ingredient.type == PELLETS:
            util = util * 1.1
        ibu = util * (alfa * weight / batch_size * 10)
        total_ibu += ibu
    return int(total_ibu)


def get_i25_j25(recipe: object) -> dict:
    """
    Calculate i25 and j25 elements for pH
    """
    try:
        grain = recipe.grainingredients_set.all()
        total_grain = float(grain.aggregate(Sum('amount'))['amount__sum'])
        mash_water = float(recipe.mash_water)
        I25 = 0
        for i in grain:
            aabb = float(i.amount) * 2.21
            if i.ingredient.category == 4:
                I25 += aabb * ((0.28 * float(i.ingredient.color)) - 2.7)
            elif i.ingredient.category == 3:
                I25 += aabb * 95
            elif i.ingredient.category == 2:
                I25 += aabb * 38
            elif i.ingredient.category == 1:
                I25 += aabb * ((0.21 * float(i.ingredient.color)) + 2.5)
            else:
                I25 += aabb * (0.28 * float(i.ingredient.color))
        C19 = mash_water / total_grain
        J25 = (0.4792 * C19)
        return {'I25': I25, 'J25': J25}
    except Exception as err:
        return {'I25': 0, 'J25': 0}





def t(cirr: str) -> str:
    """
    Transliterate a string from Cyrillic to Latin
    """
    return translit(cirr, language_code='ru', reversed=True)


def export_beerxml(r: object) -> str:
    """
    Export recipe in BeerXML
    return:
    """
    recipes = etree.Element('RECIPES')
    hops = etree.Element('HOPS')
    fermentables = etree.Element('FERMENTABLES')
    yeasts = etree.Element('YEASTS')
    miscs = etree.Element('MISCS')
    mash_steps = etree.Element('MASH_STEPS')
    # RECIPE
    recipe = E.RECIPE(
        E.NAME(r.name),
        E.VERSION('1'),
        E.TYPE('All Grain'),
        E.BREWER(r.user.username),
        E.BATCH_SIZE(str(r.batch_size)),
        E.BOIL_SIZE(str(r.pre_boil_size)),
        E.BOIL_TIME(str(r.boil_time)),
        E.EFFICIENCY(str(r.efficiency_mash)),
        E.NOTES(r.description),
    )
    # HOPS
    hps = r.hopsingredients_set.all()
    for h in hps:
        hop = E.HOP(
            E.NAME(h.ingredient.name),
            E.VERSION('1'),
            E.ALPHA(str(h.alfa)),
            E.AMOUNT(str(float(h.amount) / 1000)),
        )
        if h.use == USE_BOIL:
            hop.append(E.TIME(str(h.time)))
            hop.append(E.USE('Boil'))
        elif h.use == USE_HOP_STAND:
            hop.append(E.TIME(str(h.time)))
            hop.append(E.USE('Aroma'))
        elif h.use == USE_PRIMARY:
            hop.append(E.TIME(str(float(h.time) * 1440)))
            hop.append(E.USE('Dry Hop'))
        hops.append(hop)
    recipe.append(hops)
    # FERMENTABLES
    grains = r.grainingredients_set.all()
    for g in grains:
        grain = E.FERMENTABLE(
            E.NAME(g.ingredient.name),
            E.VERSION('1'),
            E.TYPE('Grain'),
            E.AMOUNT(str(g.amount)),
            E.YIELD(str(g.ingredient.extractivity)),
            E.COLOR(str(g.ingredient.color)),
        )
        if g.note:
            grain.append(E.NOTES(g.note))
        fermentables.append(grain)
    ferms = r.fermentableingredients_set.filter(use=USE_MASH)
    for f in ferms:
        ferm = E.FERMENTABLE(
            E.NAME(f.ingredient.name),
            E.VERSION('1'),
            E.AMOUNT(str(f.amount)),
            E.YIELD(str(f.ingredient.extractivity)),
            E.COLOR(str(f.ingredient.color)),
        )
        if f.note:
            ferm.append(E.NOTES(f.note))
        if f.ingredient.type == SUGAR:
            ferm.append(E.TYPE('Sugar'))
        elif f.ingredient.type == EXTRACT:
            ferm.append(E.TYPE('Extract'))
        else:
            ferm.append(E.TYPE('Adjunct'))
        fermentables.append(ferm)
    recipe.append(fermentables)
    # YEASTS
    ysts = r.yeastsingredients_set.all()
    for y in ysts:
        yeast = E.YEAST(
            E.NAME(y.ingredient.name),
            E.VERSION('1'),
            E.AMOUNT(str(y.amount)),
        )
        if y.ingredient.its_dry:
            yeast.append(E.FORM('Dry'))
        else:
            yeast.append(E.FORM('Liquid'))
        if y.ingredient.type == ALE:
            yeast.append(E.TYPE('Ale'))
        elif y.ingredient.type == LAGERS:
            yeast.append(E.TYPE('Lager'))
        elif y.ingredient.type == WHEAT:
            yeast.append(E.TYPE('Wheat'))
        else:
            yeast.append(E.TYPE('Wine'))
        yeasts.append(yeast)
    recipe.append(yeasts)
    # MISC
    msc = r.miscingredients_set.all()
    for m in msc:
        misc = E.MISC(
            E.NAME(m.ingredient.name),
            E.VERSION('1'),
            E.AMOUNT(str(m.amount)),
        )
        if m.measure == GRAM or m.measure == KILOGRAM:
            misc.append(E.AMOUNT_IS_WEIGHT('TRUE'))
        if m.use == USE_BOIL:
            misc.append(E.USE('Boil'))
        elif m.use == USE_HOP_STAND or m.use == USE_PRIMARY:
            misc.append(E.USE('Primary'))
        elif m.use == USE_SECONDARY:
            misc.append(E.USE('Secondary'))
        elif m.use == USE_BOTTLING:
            misc.append(E.USE('Bottling'))
        else:
            misc.append(E.USE('Mash'))
        if m.ingredient.type == SPICE:
            misc.append(E.TYPE('Spice'))
        elif m.ingredient.type == WATER_AGENT:
            misc.append(E.TYPE('Water Agent'))
        elif m.ingredient.type == HERBS:
            misc.append(E.TYPE('Herb'))
        elif m.ingredient.type == FINING:
            misc.append(E.TYPE('Fining'))
        elif m.ingredient.type == FLAVOR:
            misc.append(E.TYPE('Flavor'))
        else:
            misc.append(E.USE('Other'))
        miscs.append(misc)
    recipe.append(miscs)
    # WATER
    if hasattr(r, 'wateringredient'):
        water = E.WATER(
            E.NAME(r.name),
            E.VERSION('1'),
            E.AMOUNT(str(float(r.mash_water) + float(r.sparge_water))),
            E.CALCIUM(str(r.wateringredient.calcum)),
            E.BICARBONATE(str(r.wateringredient.bicarbonate)),
            E.SULFATE(str(r.wateringredient.sulfate)),
            E.CHLORIDE(str(r.wateringredient.chloride)),
            E.SODIUM(str(r.wateringredient.sodium)),
            E.MAGNESIUM(str(r.wateringredient.magnesium)),
            E.PH(str(r.wateringredient.ph)),
        )
        recipe.append(water)
    # STYLE
    style = E.STYLE (
        E.NAME(r.style.name),
        E.VERSION('1'),
        E.CATEGORY(TYPE_BEER[r.type]),
        E.CATEGORY_NUMBER(''),
        E.STYLE_LETTER(str(r.style.index)),
        E.STYLE_GUIDE(f'BJCP {r.style.bjcp}'),
        E.TYPE('Mixed'),
        E.OG_MIN(str(r.style.OG_min)),
        E.OG_MAX(str(r.style.OG_max)),
        E.FG_MIN(str(r.style.FG_min)),
        E.FG_MAX(str(r.style.FG_max)),
        E.IBU_MIN(str(r.style.IBUs_min)),
        E.IBU_MAX(str(r.style.IBUs_max)),
        E.COLOR_MIN(str(r.style.SRM_min)),
        E.COLOR_MAX(str(r.style.SRM_max)),
    )
    recipe.append(style)
    # MASH
    mshs = r.mashguidelines_set.all()
    mashs = E.MASH(
        E.NAME('Custom mash steps'),
        E.VERSION('1'),
        E.GRAIN_TEMP(str(20)),
    )
    for ms in mshs:
        mash_step = E.MASH_STEP(
            E.NAME(TYPE_REST[ms.type_rest]),
            E.VERSION('1'),
            E.TYPE(TYPE_HEATING[ms.type_mash]),
            E.STEP_TEMP(str(ms.step_temp)),
            E.STEP_TIME(str(ms.step_time)),
            E.DESCRIPTION(ms.note),
        )
        if ms.note:
            mash_step.append(E.DESCRIPTION(ms.note))
        mash_steps.append(mash_step)
    mashs.append(mash_steps)
    recipe.append(mashs)
    # EQUIPMENT
    equipments = E.EQUIPMENT(
        E.NAME(TYPE_REST[ms.type_rest]),
        E.VERSION('1'),
        E.BATCH_SIZE(str(r.batch_size)),
        E.BOIL_SIZE(str(r.pre_boil_size)),
    )
    recipe.append(equipments)
    recipes.append(recipe)
    return etree.tostring(recipes, pretty_print=True, xml_declaration=True, encoding='ISO-8859-1')
