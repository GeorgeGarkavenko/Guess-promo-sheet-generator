"""
Groups the aggregate of adjustments by event field into promo sheet and into CSV file
"""
import glob
import logging
import os
import sys
import ConfigParser

from app.adjustment import Adjustment
from app.color_map import ColorMap
from app.promo_sheet import PromoSheet

PROPERTY_FILE = '/home/georgeg/work/guess_promo_sheet/properties/Guess.properties'
PROPERTY_SECTION = 'PROMO_SHEET'
READ_FILE_OPTION = 'r'
INPUT_DELIMITER = '|'

class PromoGenerator(object):
    """
    Main class for gene
    """

    def __init__(self, property_file):
        self.adjustments = []
        self.logger = None

        self.configuration = self.upload_configuration(property_file)
        self.logger = self.init_logger(self.configuration, 'generator')
        self.adjustments_logger = self.init_logger(self.configuration, 'adjustment')

        self.input_dir = self.configuration.get(PROPERTY_SECTION, "input_dir")
        self.output_dir = self.configuration.get(PROPERTY_SECTION, "output_dir")

        """
        format: pipe delimited file; key: style_code
        field names: style_code,
            Category, Department_Inclusions, SubDepartment_Inclusions, Class_Inclusions,
            POS_Incslusions, Department_Exclusions, SubDepartment_Exclusions, Class_Exclusions,
            Notes_Exclusions
        """
        other_data_file = os.path.join(self.input_dir, self.configuration.get(PROPERTY_SECTION, "other_info"))
        """
        format: pipe delimited file; key: adjustment_oid
        field names: adjustment_oid, marchandising_signage
        """
        merchandising_file = os.path.join(self.input_dir,
                                          self.configuration.get(PROPERTY_SECTION, "marchandising_info"))

        """ color map from item info """
        item_info_template = self.configuration.get(PROPERTY_SECTION, "item_info")

        self.other_data = self.upload_other_data(other_data_file)
        self.marchandising_signage = self.upload_other_data(merchandising_file)
        self.color_map = ColorMap(self.logger, self.input_dir, item_info_template)

    def upload_configuration(self, property_file):
        configuration = ConfigParser.ConfigParser()
        configuration.read(property_file)
        if not configuration.has_section(PROPERTY_SECTION):
            raise Exception("There are no PROMO_SHEET section in {0}, or file do not exist".format(property_file))

        return configuration

    def init_logger(self, configuration, name):
        if not configuration:
            raise Exception("Configuration is not loaded")

        log_level = configuration.get(PROPERTY_SECTION, "log_level")
        logging.basicConfig(level=eval("logging.{0}".format(log_level)))

        path = configuration.get(PROPERTY_SECTION, "output_dir")
        filename = configuration.get(PROPERTY_SECTION, "log_file")

        handler_file = os.path.join(path, filename)

        file_handler = logging.FileHandler(handler_file)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.addHandler(file_handler)

        return logger

    def upload_adjustments(self):

        path_to_files = self.configuration.get(PROPERTY_SECTION, "input_dir")
        filename = self.configuration.get(PROPERTY_SECTION, "adjustments_files")
        adjustments = glob.iglob(os.path.join(path_to_files, filename))

        for adjustment in adjustments:
            with open(adjustment, READ_FILE_OPTION) as adjustment_file:
                adjustment_event = self.configuration.get(PROPERTY_SECTION, "event_name")
                self._process_adjustment_file(adjustment_file, adjustment_event)

    def _process_adjustment_file(self, adjustment_file, adjustment_event):
        header_line_letter = 'A'
        for line in adjustment_file:
            fields = line.split(INPUT_DELIMITER)
            line_type = fields[0].strip()

            is_header_with_adjustment_event = line_type == header_line_letter and fields[4].strip() == adjustment_event

            if is_header_with_adjustment_event:
                adjustment_file.seek(0)
                self.logger.info("Loading of adjustment OID={0}".format(fields[1].strip()))
                self.adjustments.append(Adjustment(adjustment_file, self.adjustments_logger))
                break

    def upload_other_data(self, other_item_info):
        """
        Upload other data from temporary unknown sources
        format: pipe delimited file; key: style_code
        field names: style_code,
            Category, Department_Inclusions, SubDepartment_Inclusions, Class_Inclusions,
            POS_Incslusions, Department_Exclusions, SubDepartment_Exclusions, Class_Exclusions,
            Notes_Exclusions
        """
        other_data = {}
        with open(other_item_info, READ_FILE_OPTION) as item_info_file:
            lines = [line.rstrip().split(INPUT_DELIMITER) for line in item_info_file]
            other_data = dict((row[0], row[1:]) for row in lines)
        self.logger.info("Additional data loaded: {0}".format(other_item_info))
        return other_data

    def form_promo_sheet(self):

        promoSheet = PromoSheet(self)
        promoSheet.form_records()
        promoSheet.export_csv()
        promoSheet.export_xls()

if __name__ == '__main__':

    arguments = sys.argv
    property_file = PROPERTY_FILE
    SCRIPT_NAME = arguments[0]
    MAX_ARGUMENTS = 2

    if len(arguments) > MAX_ARGUMENTS:

        print "Usage: {0} [<property file>]".format(SCRIPT_NAME)
        raise SystemExit
    elif len(arguments) == MAX_ARGUMENTS:
        property_file = arguments[1]

    promoGenerator = None

    try:
        promoGenerator = PromoGenerator(property_file)
        promoGenerator.upload_adjustments()
        promoGenerator.form_promo_sheet()
    except:
        if promoGenerator and promoGenerator.logger:
            promoGenerator.logger.error("Error in processing file {0}".format(sys.exc_value))
        else:
            sys.stderr.write("Error in processing property file {0}".format(property_file))
        sys.exit(1)
