from src.parsers.realt_parser_class import RealtParser
from src.parsers.gohome_parser_class import GohomeParser

realt_parser = RealtParser()
gohome_parser = GohomeParser()
USED_PARSERS = [realt_parser, gohome_parser]

PARSE_EVERY_MINUTES = 3
POST_EVERY_MINUTES = 1
ARCHIVE_AT = '00:00'

SUBSCRIPTION_TYPES = [('city', 'по населенному пункту', '✍ Напишите название населенного пункта'),
                      ('price', 'по стоимости м²', '✍ Напишите максимальную стоимость квадратного метра в бел. рублях')]
