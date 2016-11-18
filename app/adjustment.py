import datetime

class Adjustment(object):
    DATA_TYPES = {
        "A": "add_header",
        "D": "add_description",
        "S": "add_schedule",
        "U": "add_user_hierarchy_node",
        "C": "add_customer_hierarchy_node",
        "L": "add_location_hierarchy_node",
        "P": "add_product_hierarchy_node",
        "V": "add_parameters",
        "CB": "add_customer_business",
        "LB": "add_location_business",
        "I": "add_item_price"
    }

    def __init__(self, data=None, logger=None):

        self.oid = None
        self.external_id = None
        self.name = None
        self.event = None
        self.rule_name = None
        self.header_description = None
        self.description = None
        self.schedule = None

        self.hierarchy = {
            "U": [],
            "C": [],
            "L": [],
            "P": []
        }
        self.parameters = {}
        self.location_business = {}
        self.customer_business = []
        self.item_price = []
        self.logger = logger

        self.process_file(data)

    def process_file(self, file):
        """line processor that initializes empty adjustments"""
        [self.process_line(line.rstrip()) for line in file]

    def process_line(self, line):
        fields = line.split("|")
        field_type = fields[0]
        type = self.DATA_TYPES.get(field_type)
        if type:
            exec "self.%s(%s)" % (type, fields[1:])
        else:
            raise Exception("Invalid data type on line: %s" % line)

    def add_header(self, fields):
        oid, external_id, description, event, rule_name = fields
        self.oid = oid
        self.external_id = external_id
        self.header_description = description
        self.event = event
        self.rule_name = rule_name

    def add_description(self, fields):
        self.description = AdjustmentDescription(*fields)

    def add_schedule(self, fields):
        self.schedule = AdjustmentSchedule(*fields)

    def add_user_hierarchy_node(self, fields):
        self.hierarchy["U"].append(UserHierarchyNode(*fields))

    def add_customer_hierarchy_node(self, fields):
        self.hierarchy["C"].append(CustomerHierarchyNode(*fields))

    def add_location_hierarchy_node(self, fields):
        self.hierarchy["L"].append(LocationHierarchyNode(*fields))

    def add_product_hierarchy_node(self, fields):
        self.hierarchy["P"].append(ProductHierarchyNode(*fields))

    def add_parameters(self, fields):
        parameter_name = fields[0]
        self.parameters[parameter_name] = (AdjustmentParameters(*fields))

    def add_location_business(self, fields):
        location_id = fields[0]
        if not location_id in self.location_business:
            self.location_business[location_id] = LocationBusiness(*fields)

    def add_customer_business(self, fields):
        self.customer_business.append(CustomerBusiness(*fields))

    def add_item_price(self, fields):
        self.item_price.append(ItemPrice(*fields))


class AdjustmentDescription(object):
    def __init__(self, language_id, description, image):
        self.language_id = language_id
        self.description = description
        self.image = image


class AdjustmentSchedule(object):
    INPUT_DATE_FORMAT = "%Y-%m-%d"
    EXPORT_FORMATS = {
        "USA": "%m/%d/%Y",
        "CAN": "%m/%d/%Y"
    }

    def __init__(self, start_date, end_date, start_time, duration, mon, tue, wed, thu, fri, sat, sun):
        self._start_date = datetime.datetime.strptime(start_date, self.INPUT_DATE_FORMAT) if start_date else ''
        self._end_date = datetime.datetime.strptime(end_date, self.INPUT_DATE_FORMAT) if end_date else ''
        self.start_time = start_time
        self.duration = duration
        self.mon = mon
        self.tue = tue
        self.wed = wed
        self.thu = thu
        self.fri = fri
        self.sat = sat
        self.sun = sun

    def start_date(self, country="USA"):
        return datetime.datetime.strftime(self._start_date, self.EXPORT_FORMATS[country]) if self._start_date else ''

    def end_date(self, country="USA"):
        return datetime.datetime.strftime(self._end_date, self.EXPORT_FORMATS[country]) if self._end_date else ''


class AdjustmentParameters(object):
    def __init__(self, name, value, currency):
        self.name = name
        self.value = value
        self.currency = currency


class HierarchyNode(object):
    def __init__(self, node_type, include_exclude_flag, hierarchy_oid, hierarchy_name):
        self.node_type = node_type
        self.include_exclude_flag = include_exclude_flag
        self.hierarchy_oid = hierarchy_oid
        self.hierarchy_name = hierarchy_name


class UserHierarchyNode(HierarchyNode):
    def __init__(self, node_type, include_exclude_flag, hierarchy_oid, hierarchy_name):
        super(UserHierarchyNode, self).__init__(node_type, include_exclude_flag, hierarchy_oid, hierarchy_name)


class CustomerHierarchyNode(HierarchyNode):
    def __init__(self, node_type, include_exclude_flag, hierarchy_oid, hierarchy_name, customer_external_id):
        super(CustomerHierarchyNode, self).__init__(node_type, include_exclude_flag, hierarchy_oid, hierarchy_name)
        self.customer_external_id = customer_external_id


class LocationHierarchyNode(HierarchyNode):
    def __init__(self, node_type, include_exclude_flag, hierarchy_oid, hierarchy_name, location_external_id):
        super(LocationHierarchyNode, self).__init__(node_type, include_exclude_flag, hierarchy_oid, hierarchy_name)
        self.location_external_id = location_external_id


class ProductHierarchyNode(HierarchyNode):
    def __init__(self, node_type, include_exclude_flag, hierarchy_oid, hierarchy_name, product_group_id, item_name):
        super(ProductHierarchyNode, self).__init__(node_type, include_exclude_flag, hierarchy_oid, hierarchy_name)
        self.product_group_id = product_group_id
        self.item_name = item_name


class LocationBusiness(object):
    def __init__(self, external_id, pricing_zone, business_unit):
        self.external_id = external_id  # store id
        self.pricing_zone = pricing_zone
        self.business_unit = business_unit

    def __repr__(self):  # pragma: no cover
        return "<LocationBusiness: store id=%s, pricing zone=%s, business unit=%s>" % \
               (self.external_id, self.pricing_zone, self.business_unit)

class CustomerBusiness(object):
    def __init__(self, external_id):
        self.external_id = external_id


class ItemPrice(object):
    def __init__(self, user_hierarchy_oid, user_hierarchy_name,
                 customer_hierarchy_oid, customer_hierarchy_name, customer_external_id,
                 location_hierarchy_oid, location_hierarchy_name, location_external_id,
                 start_date, end_date, product_group_id, item_style_code, item_color, variant_item_name,
                 item_price, currency):
        self.user_hierarchy_oid = user_hierarchy_oid
        self.user_hierarchy_name = user_hierarchy_name

        self.customer_hierarchy_oid = customer_hierarchy_oid
        self.customer_hierarchy_name = customer_hierarchy_name
        self.customer_external_id = customer_external_id

        self.location_hierarchy_oid = location_hierarchy_oid
        self.location_hierarchy_name = location_hierarchy_name
        self.location_external_id = location_external_id

        self.start_date = start_date
        self.end_date = end_date
        self.product_group_id = product_group_id
        self.item_style_code = item_style_code
        self.item_color = item_color
        self.variant_item_name = variant_item_name
        self.item_price = item_price
        self.currency = currency
