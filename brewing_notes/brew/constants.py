from django.utils.translation import ugettext_lazy as _


PUNISHED = -1
DUBIOUS = 0
USER = 1
PREMIUM = 2
ENTITY = 3
MODERATOR = 10
ADMIN = 100

STATUS_USER = (
    (PUNISHED, _('Punished')),
    (DUBIOUS, _('Dubious')),
    (USER, _('User')),
    (PREMIUM, _('Premium')),
    (ENTITY, _('Entity')),
    (MODERATOR, _('Moderator')),
    (ADMIN, _('Administrator')),
)


CONFORMITY_OTHER = 0
CONFORMITY_NORMAL = 1
CONFORMITY_CLASSICAL = 2
CONFORMITY_FOR_BEGINNER = 3
CONFORMITY_TRANSFERRED = 4

STATUS_CONFORMITY = (
    (CONFORMITY_OTHER, _('Other')),
    (CONFORMITY_NORMAL, _('Normal')),
    (CONFORMITY_CLASSICAL, _('Classical')),
    (CONFORMITY_FOR_BEGINNER, _('For beginner')),
    (CONFORMITY_TRANSFERRED, _('Transferred')),
)


MASH_IN = 0
ACID_REST = 1
BETA_GLUCANASE_REST = 2
PROTEIN_REST = 3
MALTOSE_REST = 4
SACCHARIFICATION_REST = 5
DEXTRIN_REST = 6
MASH_OUT = 7

TYPE_REST = (
    (MASH_IN, _('Mash in')),
    (ACID_REST, _('Acid rest')),
    (BETA_GLUCANASE_REST, _('Beta-glucanase rest')),
    (PROTEIN_REST, _('Protein rest')),
    (MALTOSE_REST, _('Maltose rest')),
    (SACCHARIFICATION_REST, _('Saccharification rest')),
    (DEXTRIN_REST, _('Dextrin rest')),
    (MASH_OUT, _('Mash out')),
)


INFUSION = 0
DECOCTION = 1
TEMPERATURE = 2

TYPE_HEATING = (
    (INFUSION, _('Infusion')),
    (DECOCTION, _('Decoction')),
    (TEMPERATURE, _('External heating')),
)


USE_BOIL = 0
USE_HOP_STAND = 1
USE_PRIMARY = 2
USE_SECONDARY = 3
USE_BOTTLING = 4
USE_MASH = 5

USE = (
    (USE_BOIL, _('On boil')),
    (USE_HOP_STAND, _('Hop stand')),
    (USE_PRIMARY, _('On fermentation')),
    (USE_BOTTLING, _('On bottling')),
    (USE_MASH, _('On mash')),
)

MINUTES = 0
GRAM = 1
KILOGRAM = 2
MILLILITER = 3
LITER = 4
BAR = 5
PSI = 6
PIECES = 7

MEASURE = (
    (MINUTES, _('min')),
    (GRAM, _('g')),
    (KILOGRAM, _('kg')),
    (MILLILITER, _('ml')),
    (LITER, _('l')),
    (BAR, _('Bar')),
    (PSI, _('psi')),
    (PIECES, _('pieces')),
)


CORN_SUGAR = 0
CO2 = 1
WORT = 2
DME = 3
OTHER = 4

PRIMING_METHOD = (
    (CORN_SUGAR, _('Corn sugar')),
    (CO2, _('CO2 keg')),
    (WORT, _('Wort / Speise')),
    (DME, _('DME')),
    (OTHER, _('Other')),
)

LOG_PRIMARY = 0
LOG_BREW = 1
LOG_SECONDARY = 2
LOG_COLD_CRASH = 3
LOG_CARBONISATION = 4
LOG_BOTTLING = 5
LOG_NOTE = 6
LOG_DRY_HOP = 7
LOG_OTHER = 99

LOG_EVENT = (
    (LOG_PRIMARY, _('Primary fermentation')),
    (LOG_BREW, _('Brew')),
    (LOG_SECONDARY, _('Secondary fermentation')),
    (LOG_COLD_CRASH, _('Cold crash')),
    (LOG_CARBONISATION, _('Carbonisation')),
    (LOG_BOTTLING, _('Bottling')),
    (LOG_NOTE, _('Note')),
    (LOG_DRY_HOP, _('Dry hop')),
    (LOG_OTHER, _('Other')),
)

FERM_OTHER = 0
FERM_PRIMARY = 1
FERM_SECONDARY = 2
FERM_LAGERING = 3
FERM_COLD_CRASH = 4
FERM_MATURATION = 5
FERM_DRY_HOP = 6
FERM_CARBONISATION = 7

TYPE_FERMENTATION = (
    (FERM_OTHER, _('Other')),
    (FERM_PRIMARY, _('Primary fermentation')),
    (FERM_SECONDARY, _('Secondary fermentation')),
    (FERM_LAGERING, _('Lagering')),
    (FERM_COLD_CRASH, _('Cold crash')),
    (FERM_MATURATION, _('Maturation')),
    (FERM_DRY_HOP, _('Dry hop')),
    (FERM_CARBONISATION, _('Carbonisation')),
)

DEVICE_BREWPILESS = 0
DEVICE_ISPINDEL = 1
# DEVICE_BNC_MODULE = 10
# DEVICE_OTHER = 99

DEVICE_TYPE = (
    (DEVICE_BREWPILESS, 'BrewPiLess'),
    (DEVICE_ISPINDEL, 'iSpindel'),
    # (DEVICE_BNC_MODULE, 'BNC-module'),
    # (DEVICE_OTHER, _('Other device')),
)

EQUIPMENT_FERMENTER = 0
EQUIPMENT_KETTLE = 1
EQUIPMENT_BIAB = 2
EQUIPMENT_KRIMS_TT = 3
EQUIPMENT_KRIMS_SL = 4
# EQUIPMENT_BIAB_2K = 3
# EQUIPMENT_HERMS = 6
# EQUIPMENT_OTHER = 99

EQUIPMENT_TYPE = (
    (EQUIPMENT_FERMENTER, _('Fermenter')),
    (EQUIPMENT_KETTLE, _('Kettle')),
    (EQUIPMENT_BIAB, _('BIAB system')),
    (EQUIPMENT_KRIMS_TT, _('K-RIMS two tier system')),
    (EQUIPMENT_KRIMS_SL, _('K-RIMS single-level system')),
    # (EQUIPMENT_BIAB_2K, 'BIAB two kettle system'),
    # (EQUIPMENT_HERMS, 'HERMS system'),
    # (EQUIPMENT_OTHER, _('Other system')),
)


MODULE_OM_NONE = 0
MODULE_OM_FERMENTER_COOLER = 11
MODULE_OM_FERMENTER_HEATER = 12
MODULE_OM_KETTLE = 21
MODULE_OM_BIAB_HEATER = 31
MODULE_OM_BIAB_PUMP = 32
MODULE_OM_KRIMS_TT_HEATER = 41
MODULE_OM_KRIMS_TT_PUMP = 42
MODULE_OM_KRIMS_SL_HEATER = 51
MODULE_OM_KRIMS_SL_PUMP_H = 52
MODULE_OM_KRIMS_SL_PUMP_M = 53


MODULE_OPERATION_MODE = (
    (MODULE_OM_NONE, _('No mode')),
    (MODULE_OM_FERMENTER_COOLER, _('Fermenter: cooler')),
    (MODULE_OM_FERMENTER_HEATER, _('Fermenter: heater')),
    (MODULE_OM_KETTLE, _('Kettle')),
    (MODULE_OM_BIAB_HEATER, _('BIAB: heater')),
    (MODULE_OM_BIAB_PUMP, _('BIAB: pump')),
    (MODULE_OM_KRIMS_TT_HEATER, _('K-RIMS two tier: heater')),
    (MODULE_OM_KRIMS_TT_PUMP, _('K-RIMS two tier: pump')),
    (MODULE_OM_KRIMS_SL_HEATER, _('K-RIMS single-level: heater')),
    (MODULE_OM_KRIMS_SL_PUMP_H, _('K-RIMS single-level: pump (HLT)')),
    (MODULE_OM_KRIMS_SL_PUMP_M, _('K-RIMS single-level: pump (MLT)')),
)

MODE_MATCHING = {
    EQUIPMENT_FERMENTER: [MODULE_OM_FERMENTER_COOLER, MODULE_OM_FERMENTER_HEATER],
    EQUIPMENT_KETTLE: [MODULE_OM_KETTLE, ],
    EQUIPMENT_BIAB: [MODULE_OM_BIAB_HEATER, MODULE_OM_BIAB_PUMP],
    EQUIPMENT_KRIMS_TT: [MODULE_OM_KRIMS_TT_HEATER, MODULE_OM_KRIMS_TT_PUMP],
    EQUIPMENT_KRIMS_SL: [MODULE_OM_KRIMS_SL_HEATER, MODULE_OM_KRIMS_SL_PUMP_H, MODULE_OM_KRIMS_SL_PUMP_M],
}


WATER_ADD_GYPSUM = 0
WATER_ADD_CALCIUM_CHLORIDE = 1
WATER_ADD_EPSOM = 2
WATER_ADD_MAGNESIUM_CHLORIDE = 3
WATER_ADD_CANNING_SALT = 4
WATER_ADD_BAKING_SODA = 5
WATER_ADD_CHALK = 6
WATER_ADD_PICKLING_LIME = 7

WATER_ADD_LACTIC_ACID = 21
WATER_ADD_CITRIC_ACID = 22
WATER_ADD_ACETIC_ACID = 23
WATER_ADD_PHOSPHORIC_ACID = 24

WATER_ADD_OTHER = 99

WATER_ADDITIVE = (
    (WATER_ADD_GYPSUM, _('Gypsum')),
    (WATER_ADD_CALCIUM_CHLORIDE, _('Calcium Chloride')),
    (WATER_ADD_EPSOM, _('Epsom Salt')),
    (WATER_ADD_MAGNESIUM_CHLORIDE, _('Magnesium Chloride')),
    (WATER_ADD_CANNING_SALT, _('Canning Salt')),
    (WATER_ADD_BAKING_SODA, _('Baking Soda')),
    (WATER_ADD_CHALK, _('Chalk')),
    (WATER_ADD_PICKLING_LIME, _('Pickling Lime')),
    (WATER_ADD_LACTIC_ACID, _('Lactic Acid')),
    (WATER_ADD_CITRIC_ACID, _('Citric Acid')),
    (WATER_ADD_ACETIC_ACID, _('Acetic Acid')),
    (WATER_ADD_PHOSPHORIC_ACID, _('Phosphoric Acid')),
    (WATER_ADD_OTHER, _('Other')),
)

SRM = {
    0: '#FFF4D4',
    1: '#FFE699',
    2: '#FFD878',
    3: '#FFCA5A',
    4: '#FFBF42',
    5: '#FBB123',
    6: '#F8A600',
    7: '#F39C00',
    8: '#EA8F00',
    9: '#E58500',
    10: '#DE7C00',
    11: '#D77200',
    12: '#CF6900',
    13: '#CB6200',
    14: '#C35900',
    15: '#BB5100',
    16: '#B54C00',
    17: '#B04500',
    18: '#A63E00',
    19: '#A13700',
    20: '#9B3200',
    21: '#952D00',
    22: '#8E2900',
    23: '#882300',
    24: '#821E00',
    25: '#7B1A00',
    26: '#771900',
    27: '#701400',
    28: '#6A0E00',
    29: '#660D00',
    30: '#5E0B00',
    31: '#5A0A02',
    32: '#600903',
    33: '#520907',
    34: '#4C0505',
    35: '#470606',
    36: '#420607',
    37: '#3D0708',
    38: '#370607',
    39: '#2D0607',
    40: '#1F0506',
    41: '#000000',
}
