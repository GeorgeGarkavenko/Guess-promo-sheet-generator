import csv
import calendar
import datetime
import os

PROPERTY_SECTION = 'PROMO_SHEET'
WRITE_FILE_OPTION = 'wb'
OUTPUT_DELIMITER = '\t'
DEFAULT_COUNTRY = 'USA'


class PromoSheet(object):
    """
    Model of promo sheet
    """

    def __init__(self, generator=None):
        self.title = '{country} USA MARCIANO STORES (INCLUDES {year}) - {month} WEEK {week_number}'
        self.effective = 'Effective: {start_date}   {end_date}'
        self.country = ''
        self.start_date = ''
        self.end_date = ''

        self.header_promo_effective = 'PROMO SHEET EFFECTIVE {start_date} {end_date}'
        self.headers = ['INCLUSIONS', 'EXCLUSIONS', 'NOTES']

        self.columns = \
            ['Category', 'Promotion', 'Style #', 'COLOR', 'STYLE DESCRIPTION', 'MERCHANDISING/SIGNAGE',
             'DEPT', 'SUBDEPT', 'CLASS', 'POS?', 'DEPT', 'SUBDEPT', 'CLASS', 'NOTES','']

        self.generator = generator

        self.records = []

        self.footer = ['*NEW PROMOTIONS AND ANY    CHANGES ARE BOLDED AND HIGHLIGHTED IN GREY']

    def form_records(self):
        """
        Simplified promo sheet rows generation algorithm
        TODO: check adjustments items styles/colors processing
        """
        ALL_COLLORS = 'ALL'
        ALL_COLLORS_QUANTITY = 2
        EMPTY_OTHER_INFO_ROW_PART = ['', '', '', '', '', '', '', '', '']

        if not self.generator:
            self.records = []
            return None

        generator = self.generator

        adjustments_list, color_map, other_info, marchandising_signage, logger =\
            generator.adjustments, \
            generator.color_map, \
            generator.other_data, \
            generator.marchandising_signage,  \
            generator.logger

        result = []

        for adjustment in adjustments_list:
            # update country and period
            self.update_country(adjustment)
            self.update_period(adjustment)

            # process styles/colors
            adjustment_item_styles = set(item_price.item_style_code for item_price in adjustment.item_price)
            possible_styles = color_map.keys()

            current_adjustment_styles = \
                {style:  ([ALL_COLLORS, color_map.get_colors(style).values()[0][1]]
                          if len(color_map.get_colors(style).values()) >= ALL_COLLORS_QUANTITY else
                          list(color_map.get_colors(style).values()[0]))
                 for style in adjustment_item_styles
                 if style in possible_styles}

            # form a data row for output

            a_row = [[adjustment.parameters['PromoCategory'].value,
                      adjustment.header_description,
                      style]
                     + current_adjustment_styles[style]
                     + marchandising_signage.get(adjustment.oid, '')
                     + other_info.get(style, EMPTY_OTHER_INFO_ROW_PART)[1:]
                     for style in adjustment_item_styles
                     if style in possible_styles]
            # append new data row
            result.extend(a_row)
        self.records = result

    def update_country(self, adjustment):
        country_parameter = adjustment.parameters.get('Country')
        if not country_parameter:
            self.generator.logger.error(
                "There are no country parameter in adjustment OID={0}. Used {1}".format(adjustment.oid,
                                                                                        DEFAULT_COUNTRY))
            if not self.country:
                self.country = DEFAULT_COUNTRY
                self.generator.logger.info(
                    "Used default country {0}".format(DEFAULT_COUNTRY))
        elif not self.country:

            self.country = country_parameter.value

        elif self.country is not country_parameter.value:
            self.generator.logger.warning(
                "Country value in adjustment OID={0} is diferent ({1})".format(adjustment.oid,
                                                                               country_parameter.value))

    def update_period(self, adjustment):
        schedule = adjustment.schedule

        if not schedule:
            self.generator.logger.warning("There are no schedule in adjustment OID={0}".format(adjustment.oid))
            return None

        if not schedule._start_date or not schedule._end_date:
            self.generator.logger.warning(
                "The periond in adjustment schedule is not defined in adjustment OID={0}".format(adjustment.oid))
        else:
            start, end = (schedule.start_date(self.country), schedule.end_date(self.country)) if self.country else \
                (schedule.start_date(), schedule.end_date())
            if not self.start_date and not self.end_date:
                self.start_date, self.end_date = start, end
            elif not ((self.start_date, self.end_date) == (start, end)):
                self.generator.logger.warning(
                    "The dates in schedule adjustment OID={0} are different".format(adjustment.oid))

    def export_csv(self):
        """
        Form csv model of prom sheet
        """
        export_date_format = "%m/%d/%Y"
        csv_name = self.generator.configuration.get(PROPERTY_SECTION, "output_csv_file")
        csv_path = os.path.join(self.generator.output_dir, csv_name)

        self.generator.logger.info("Writing CSV file: {0}".format(csv_path))
        with open(csv_path, WRITE_FILE_OPTION) as csv_file:
            # {country} USA MARCIANO STORES (INCLUDES {year}) - {month} WEEK {week_number}

            date = datetime.datetime.strptime(self.start_date, export_date_format)
            year, week_number, day = date.isocalendar()

            title = self.title.format(country=self.country, year=year,
                                      month=calendar.month_name[date.month], week_number=week_number)
            effective_period = self.effective.format(start_date=self.start_date, end_date=self.end_date)

            # PROMO SHEET EFFECTIVE {start_date} {end_date}
            effective_dates = [self.header_promo_effective.format(start_date=self.start_date, end_date=self.end_date)]
            all_rows = [[title, effective_period], effective_dates + self.headers, self.columns]
            all_rows.extend(self.records)
            all_rows.extend([self.footer])
            writer = csv.writer(csv_file, dialect=csv.excel, delimiter=OUTPUT_DELIMITER)
            [writer.writerow(row) for row in all_rows]

    def export_xls(self):
        """
        Form prom sheet
        """
        pass
