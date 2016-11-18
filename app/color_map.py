import collections
import glob
import os

READ_FILE_OPTION = 'r'
INPUT_DELIMITER = '|'


class ColorMap(object):
    """
    Colors two-dimensional map (style_code, variant_code)
    """
    def __init__(self, logger, path_to_files, filename):
        INCLUDE_COLOR_VALUE = '0'
        try:
            files_list = glob.iglob(os.path.join(path_to_files, filename))
            self.item_info_name = max(files_list, key=os.path.getctime)
        except ValueError:
            message = "Cannot find any item information files from {0}".format(path_to_files)
            logger.error(message)
            raise SystemExit(message)

        self._color_map = collections.defaultdict(dict)
        self.filter_counter = 0

        ItemInfo = collections.namedtuple('ItemInfo',
                                          ['variant_code', 'description', 'a', 'style_code', 'c', 'd', 'e', 'f',
                                           'color',
                                           'size', 'g', 'filter_code', 'h'])
        with open(self.item_info_name, READ_FILE_OPTION) as item_info_file:
            lines = [line.split(INPUT_DELIMITER) for line in item_info_file]

            for item in map(ItemInfo._make, lines):
                if item.filter_code <> INCLUDE_COLOR_VALUE:  # TODO: check out the exclude color variants
                    self.filter_counter += 1
                    continue
                self._color_map[item.style_code][item.variant_code] = (item.color, item.description)

        logger.info("Color map loaded: {0}".format(self.item_info_name))

    def get_colors(self, style_id):
        return self._color_map.get(style_id)

    def keys(self):
        return self._color_map.keys()
