from django.utils.translation import ugettext_lazy as _


BJCP_2015 = 0
BJCP_2021 = 1

BEER_STYLE_GUIDELINES = (
    (BJCP_2015, _('BJCP 2015')),
    (BJCP_2021, _('BJCP 2021')),
)


LIGHT_LAGER = 0
PILSNER = 1
AMBER_LAGER = 2
DARK_LAGER = 3
BOCK = 4
IPA = 5
LIGHT_ALE = 6
AMBER_ALE = 7
BROWN_ALE = 8
STRONG_ALE = 9
SOUR_ALE = 10
PORTER = 11
STOUT = 12
WHEAT_BEER = 13
SPECIAL_BEER = 14

TYPE_BEER = (
    (LIGHT_LAGER, _('Light lager')),
    (PILSNER, _('Pilsner')),
    (AMBER_LAGER, _('Amber lager')),
    (DARK_LAGER, _('Dark lager')),
    (BOCK, _('Bock')),
    (IPA, _('IPA')),
    (LIGHT_ALE, _('Light ale')),
    (AMBER_ALE, _('Amber Ale')),
    (BROWN_ALE, _('Brown Ale')),
    (STRONG_ALE, _('Strong Ale')),
    (SOUR_ALE, _('Sour Ale')),
    (PORTER, _('Porter')),
    (STOUT, _('Stout')),
    (WHEAT_BEER, _('Wheat beer')),
    (SPECIAL_BEER, _('Special beer'))
)


BASE_MALT = 0
SPECIALTY_MALT = 1
UNMALTED = 2
OTHERS = 3

TYPE_GRAIN = (
    (BASE_MALT, _('Base malt')),
    (SPECIALTY_MALT, _('Specialty malt')),
    (UNMALTED, _('Unmalted')),
    (OTHERS, _('Others')),
)


CATEGORY_BASE_MALT = 0
CATEGORY_CRYSTAL_MALT = 1
CATEGORY_ROAST_MALT = 2
CATEGORY_ACID_MALT = 3
CATEGORY_WHEAT_MALT = 4

MALT_CATEGORY = (
    (CATEGORY_BASE_MALT, _('Base malt')),
    (CATEGORY_CRYSTAL_MALT, _('Crystal malt')),
    (CATEGORY_ROAST_MALT, _('Roast malt')),
    (CATEGORY_ACID_MALT, _('Acid malt')),
    (CATEGORY_WHEAT_MALT, _('Wheat malt')),
)

SUGAR = 0
EXTRACT = 1
FRUIT = 2
JUICE = 3
HONEY = 4
NON_FERMENTABLE = 5
OTHERS = 99

TYPE_FERMENTABLE = (
    (SUGAR, _('Sugar')),
    (EXTRACT, _('Extract')),
    (FRUIT, _('Fruit')),
    (JUICE, _('Juice')),
    (HONEY, _('Honey')),
    (NON_FERMENTABLE, _('Non-fermentable')),
    (OTHERS, _('Others')),
)


PELLETS = 0
LEAF_WHOLE = 1
LUPULIN_PELLET = 2

TYPE_HOPS = (
    (PELLETS, _('Pellet')),
    (LEAF_WHOLE, _('Leaf whole')),
    (LUPULIN_PELLET, _('Lupulin Pellet')),
)


SPICE = 0
WATER_AGENT = 1
HERBS = 2
FINING = 3
FLAVOR = 4
ACIDS = 5
BACTERIA = 6
OTHERS = 99

TYPE_ADDITIVE = (
    (SPICE, _('Spice')),
    (WATER_AGENT, _('Water agent')),
    (HERBS, _('Herbs')),
    (FINING, _('Fining')),
    (FLAVOR, _('Flavor')),
    (ACIDS, _('Acid')),
    (BACTERIA, _('Bacteria')),
    (OTHERS, _('Other')),
)


ALE = 0
LAGERS = 1
WHEAT = 2
WINE = 3
OTHERS = 4

TYPE_YEASTS = (
    (ALE, _('Ale')),
    (LAGERS, _('Lagers')),
    (WHEAT, _('Wheat')),
    (WINE, _('Wine')),
    (OTHERS, _('Others')),
)


LOW = 0
MEDIUM = 1
HIGH = 2
VERY_HIGH = 3
UNKNOWN = 4

FLOCCULATION = (
    (LOW, _('Low')),
    (MEDIUM, _('Medium')),
    (HIGH, _('High')),
    (VERY_HIGH, _('Very High')),
    (UNKNOWN, _('Unknown')),
)
