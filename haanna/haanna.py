"""Plugwise Anna Home Assistant component."""

import requests
import datetime
import pytz
import xml.etree.cElementTree as Etree

# For python 3.6 strptime fix
import re

ANNA_PING_ENDPOINT = "/ping"
ANNA_DIRECT_OBJECTS_ENDPOINT = "/core/direct_objects"
ANNA_DOMAIN_OBJECTS_ENDPOINT = "/core/domain_objects"
ANNA_LOCATIONS_ENDPOINT = "/core/locations"
ANNA_APPLIANCES = "/core/appliances"
ANNA_RULES = "/core/rules"


class Haanna:
    """Define the Haanna object."""

    def __init__(
        self, username, password, host, port, legacy_anna=False,
    ):
        """Set the constructor for this class."""
        self.legacy_anna = legacy_anna
        self._username = username
        self._password = password
        self._endpoint = "http://" + host + ":" + str(port)

    def ping_anna_thermostat(self):
        """Ping the thermostat to see if it's online."""
        ping = requests.get(
            self._endpoint + ANNA_PING_ENDPOINT,
            auth=(self._username, self._password),
            timeout=10,
        )

        if ping.status_code != 404:
            raise ConnectionError("Could not connect to the gateway.")

        return True

    def get_direct_objects(self):
        """Collect the direct_objects XML-data."""
        xml = requests.get(
              self._endpoint + ANNA_DIRECT_OBJECTS_ENDPOINT,
              auth=(self._username, self._password),
              timeout=10,
        )

        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            raise ConnectionError("Could not get the direct objects.")

        return Etree.fromstring(self.escape_illegal_xml_characters(xml.text))

    def get_domain_objects(self):
        """Collect the domain_objects XML-data."""
        xml = requests.get(
              self._endpoint + ANNA_DOMAIN_OBJECTS_ENDPOINT,
              auth=(self._username, self._password),
              timeout=10,
        )

        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            raise ConnectionError("Could not get the domain objects.")

        return Etree.fromstring(self.escape_illegal_xml_characters(xml.text))

    @staticmethod
    def escape_illegal_xml_characters(root):
        """Replace illegal &-characters."""
        return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", root)

    def get_presets(self, root):
        """Get the presets from the thermostat."""
        if self.legacy_anna:
            return self.__get_preset_dictionary_v1(root)
        rule_id = self.get_rule_id_by_template_tag(
            root, "zone_setpoint_and_state_based_on_preset",
        )[0]

        if rule_id is None:
            rule_id = self.get_rule_id_by_name(root, "Thermostat presets")
            if rule_id is None:
                raise RuleIdNotFoundException("Could not find the rule id.")

        presets = self.get_preset_dictionary(root, rule_id)
        return presets

    def get_schema_names(self, root):
        """Get schemas or schedules available."""
        schemas = root.findall(".//rule")
        result = []
        for schema in schemas:
            rule_name = schema.find("name").text
            if rule_name:
                if self.legacy_anna:
                    if "preset" not in rule_name:
                        result.append(rule_name)
                else:
                    if "presets" not in rule_name:
                        result.append(rule_name)
        if result == []:
            return None
        return result

    def set_schema_state(self, root, schema, state):
        """Send a set request to the schema with the given name."""
        schema_rule_id = self.get_rule_id_by_name(root, str(schema))
        templates = root.findall(".//*[@id='{}']/template".format(schema_rule_id))
        template_id = None
        for rule in templates:
            template_id = rule.attrib["id"]

        uri = "{};id={}".format(ANNA_RULES, schema_rule_id)

        state = str(state)
        data = (
            '<rules><rule id="{}"><name><![CDATA[{}]]></name>'
            '<template id="{}" /><active>{}</active></rule>'
            "</rules>".format(schema_rule_id, schema, template_id, state)
        )

        xml = requests.put(
              self._endpoint + uri,
              auth=(self._username, self._password),
              data=data,
              headers={"Content-Type": "text/xml"},
              timeout=10,
        )

        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            CouldNotSetTemperatureException(
                "Could not set the schema to {}.".format(state) + xml.text
            )

        return "{} {}".format(xml.text, data)

    def get_active_schema_name(self, root):
        """Get active schema."""
        if self.legacy_anna:
            schemas = root.findall(".//rule")
            result = []
            for schema in schemas:
                rule_name = schema.find("name").text
                if "preset" not in rule_name:
                    result.append(rule_name)
            result = "".join(map(str, result))
            if result == []:
                return None
            return result

        locator = "zone_preset_based_on_time_and_presence_with_override"
        rule_id = self.get_rule_id_by_template_tag(root, locator)
        if rule_id:
            schema_active = self.get_active_name(root, rule_id)
            return schema_active

    def get_last_active_schema_name(self, root):
        """Determine the last active schema (not used for legacy Anna)."""
        if not self.legacy_anna:
            locator = "zone_preset_based_on_time_and_presence_with_override"
            rule_id = self.get_rule_id_by_template_tag(root, locator)
            last_schema_active = self.get_last_active_name(root, rule_id)
            return last_schema_active

    @staticmethod
    def get_schema_state(root):
        """Get the mode the thermostat is in (active schedule is true or false)."""
        log_type = "schedule_state"
        locator = (
            "appliance[type='thermostat']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        if root.find(locator) is not None:
            return root.find(locator).text == "on"
        return None

    @staticmethod
    def get_rule_id_by_template_tag(root, rule_name):
        """Get the rule ID based on template_tag."""
        schema_ids = []
        rules = root.findall("rule")
        for rule in rules:
            if rule.find("template").attrib["tag"] == rule_name:
                schema_ids.append(rule.attrib["id"])
        if schema_ids == []:
            return None
        return schema_ids

    def set_preset(self, root, preset):
        """Set the given preset on the thermostat."""
        if self.legacy_anna:
            return self.__set_preset_v1(root, preset)
        locator = "appliance[type='thermostat']/location"
        location_id = root.find(locator).attrib["id"]

        locations_root = Etree.fromstring(
            requests.get(
                self._endpoint + ANNA_LOCATIONS_ENDPOINT,
                auth=(self._username, self._password),
                timeout=10,
            ).text
        )

        current_location = locations_root.find("location[@id='" + location_id + "']")
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        xml = requests.put(
              self._endpoint + ANNA_LOCATIONS_ENDPOINT + ";id=" + location_id,
              auth=(self._username, self._password),
              data="<locations>"
              + '<location id="'
              + location_id
              + '">'
              + "<name>"
              + location_name
              + "</name>"
              + "<type>"
              + location_type
              + "</type>"
              + "<preset>"
              + preset
              + "</preset>"
              + "</location>"
              + "</locations>",
              headers={"Content-Type": "text/xml"},
              timeout=10,
        )

        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            raise CouldNotSetPresetException(
                "Could not set the " "given preset: " + xml.text
            )
        return xml.text

    def __set_preset_v1(self, root, preset):
        """Set the given preset on the thermostat for V1."""
        locator = "rule/directives/when/then[@icon='" + preset + "'].../.../..."
        rule = root.find(locator)
        if rule is None:
            raise CouldNotSetPresetException("Could not find preset '" + preset + "'")

        rule_id = rule.attrib["id"]
        xml = requests.put(
              self._endpoint + ANNA_RULES,
              auth=(self._username, self._password),
              data="<rules>"
              + '<rule id="'
              + rule_id
              + '">'
              + "<active>true</active>"
              + "</rule>"
              + "</rules>",
              headers={"Content-Type": "text/xml"},
              timeout=10,
        )
        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            raise CouldNotSetPresetException(
                "Could not set the given " "preset: " + xml.text
            )
        return xml.text

    @staticmethod
    def get_boiler_status(root):
        """Get the active boiler-heating status (On-Off control)."""
        log_type = "boiler_state"
        locator = (
            "appliance[type='heater_central']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        if root.find(locator) is not None:
            return root.find(locator).text == "on"
        return None

    @staticmethod
    def get_heating_status(root):
        """Get the active heating status (OpenTherm control)."""
        log_type = "central_heating_state"
        locator = (
            "appliance[type='heater_central']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        if root.find(locator) is not None:
            return root.find(locator).text == "on"
        return None

    @staticmethod
    def get_cooling_status(root):
        """Get the active cooling status."""
        log_type = "cooling_state"
        locator = (
            "appliance[type='heater_central']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        if root.find(locator) is not None:
            return root.find(locator).text == "on"
        return None

    def get_domestic_hot_water_status(self, root):
        """Get the domestic hot water status."""
        if self.legacy_anna:
            return None
        log_type = "domestic_hot_water_state"
        locator = (
            "appliance[type='heater_central']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        if root.find(locator) is not None:
            return root.find(locator).text == "on"
        return None

    def get_current_preset(self, root):
        """Get the current active preset."""
        if self.legacy_anna:
            active_rule = root.find("rule[active='true']/directives/when/then")
            if active_rule is None or "icon" not in active_rule.keys():
                return "none"
            return active_rule.attrib["icon"]

        log_type = "preset_state"
        locator = (
            "appliance[type='thermostat']/logs/point_log[type='"
            + log_type
            + "']/period/measurement"
        )
        return root.find(locator).text

    def get_schedule_temperature(self, root):
        """Get the temperature setting from the selected schedule."""
        point_log_id = self.get_point_log_id(root, "schedule_temperature")
        if point_log_id:
            measurement = self.get_measurement_from_point_log(root, point_log_id)
            if measurement:
                value = float(measurement)
                return value
        return None

    def get_current_temperature(self, root):
        """Get the curent (room) temperature from the thermostat - match to HA name."""
        current_temp_point_log_id = self.get_point_log_id(root, "temperature")
        if current_temp_point_log_id:
            measurement = self.get_measurement_from_point_log(
                root, current_temp_point_log_id
            )
            value = float(measurement)
            return value
        return None

    def get_target_temperature(self, root):
        """Get the target temperature from the thermostat."""
        target_temp_log_id = self.get_point_log_id(root, "target_temperature")
        if target_temp_log_id:
            measurement = self.get_measurement_from_point_log(root, target_temp_log_id)
            value = float(measurement)
            return value  
        return None

    def get_thermostat_temperature(self, root):
        """Get the target temperature from the thermostat."""
        thermostat_log_id = self.get_point_log_id(root, "thermostat")
        if thermostat_log_id:
            measurement = self.get_measurement_from_point_log(root, thermostat_log_id)
            value = float(measurement)
            return value
        return None

    def get_outdoor_temperature(self, root):
        """Get the temperature from the thermostat."""
        outdoor_temp_log_id = self.get_point_log_id(root, "outdoor_temperature")
        if outdoor_temp_log_id:
            measurement = self.get_measurement_from_point_log(root, outdoor_temp_log_id)
            value = float(measurement)
            value = '{:.1f}'.format(round(value, 1))
            return value
        return None

    def get_illuminance(self, root):
        """Get the illuminance value from the thermostat."""
        point_log_id = self.get_point_log_id(root, "illuminance")
        if point_log_id:
            measurement = self.get_measurement_from_point_log(root, point_log_id)
            value = float(measurement)
            value = '{:.1f}'.format(round(value, 1))
            return value
        return None

    def get_boiler_temperature(self, root):
        """Get the boiler_temperature value from the thermostat."""
        point_log_id = self.get_point_log_id(root, "boiler_temperature")
        if point_log_id:
            measurement = self.get_measurement_from_point_log(root, point_log_id)
            value = float(measurement)
            value = '{:.1f}'.format(round(value, 1))
            return value
        return None

    def get_water_pressure(self, root):
        """Get the water pressure value from the thermostat."""
        point_log_id = self.get_point_log_id(root, "central_heater_water_pressure")
        if point_log_id:
            measurement = self.get_measurement_from_point_log(root, point_log_id)
            value = float(measurement)
            value = '{:.1f}'.format(round(value, 1))
            return value
        return None

    def __get_temperature_uri(self, root):
        """Determine the set_temperature uri for different versions of Anna."""
        if self.legacy_anna:
            locator = "appliance[type='thermostat']"
            appliance_id = root.find(locator).attrib["id"]
            return ANNA_APPLIANCES + ";id=" + appliance_id + "/thermostat"
        locator = "appliance[type='thermostat']/location"
        location_id = root.find(locator).attrib["id"]
        locator = (
            "location[@id='"
            + location_id
            + "']/actuator_functionalities/thermostat_functionality"
        )
        thermostat_functionality_id = root.find(locator).attrib["id"]

        temperature_uri = (
            ANNA_LOCATIONS_ENDPOINT
            + ";id="
            + location_id
            + "/thermostat;id="
            + thermostat_functionality_id
        )
        return temperature_uri

    def set_temperature(self, root, temperature):
        """Send a set request to the temperature with the given temperature."""
        uri = self.__get_temperature_uri(root)

        temperature = str(temperature)

        xml = requests.put(
              self._endpoint + uri,
              auth=(self._username, self._password),
              data="<thermostat_functionality><setpoint>"
              + temperature
              + "</setpoint></thermostat_functionality>",
              headers={"Content-Type": "text/xml"},
              timeout=10,
        )

        if xml.status_code != requests.codes.ok:  # pylint: disable=no-member
            CouldNotSetTemperatureException("Could not set the temperature." + xml.text)

        return xml.text

    def get_anna_endpoint(self):
        """Get the ANNA Endpoint."""
        return self._endpoint

    @staticmethod
    def get_point_log_id(root, log_type):
        """Get the point log ID based on log type."""
        locator = (
            "module/services/*[@log_type='" + log_type + "']/functionalities/point_log"
        )
        if root.find(locator) is not None:
            return root.find(locator).attrib["id"]
        return None

    @staticmethod
    def get_measurement_from_point_log(root, point_log_id):
        """Get the measurement from a point log based on point log ID."""
        locator = "*/logs/point_log[@id='" + point_log_id + "']/period/measurement"
        if root.find(locator) is not None:
            return root.find(locator).text
        return None

    @staticmethod
    def get_rule_id_by_name(root, rule_name):
        """Get the rule ID based on name."""
        rules = root.findall("rule")
        for rule in rules:
            if rule.find("name").text == rule_name:
                return rule.attrib["id"]

    @staticmethod
    def get_preset_dictionary(root, rule_id):
        """Get the presets from a rule based on rule ID and returns a dictionary with all the key-value pairs."""
        preset_dictionary = {}
        directives = root.find("rule[@id='" + rule_id + "']/directives")
        for directive in directives:
            preset_dictionary[directive.attrib["preset"]] = float(
                directive.find("then").attrib["setpoint"]
            )
        return preset_dictionary

    @staticmethod
    def __get_preset_dictionary_v1(root):
        """
        Get the presets and returns a dictionary with all the key-value pairs.

        Example output: {'away': 17.0, 'home': 20.0, 'vacation': 15.0,
        'no_frost': 10.0, 'asleep': 15.0}.
        """
        preset_dictionary = {}
        directives = root.findall("rule/directives/when/then")
        for directive in directives:
            if directive is not None and "icon" in directive.keys():
                preset_dictionary[directive.attrib["icon"]] = float(
                    directive.attrib["temperature"]
                )
        return preset_dictionary

    @staticmethod
    def get_active_mode(root, schema_ids):
        """Get the mode from a (list of) rule id(s)."""
        active = False
        for schema_id in schema_ids:
            if root.find("rule[@id='" + schema_id + "']/active").text == "true":
                active = True
                break
        return active

    @staticmethod
    def get_active_name(root, schema_ids):
        """Get the active schema from a (list of) rule id(s)."""
        active = None
        for schema_id in schema_ids:
            locator = root.find("rule[@id='" + schema_id + "']/active")
            # Only one can be active
            if locator.text == "true":
                active = root.find("rule[@id='" + schema_id + "']/name").text
                return active

    @staticmethod
    def get_last_active_name(root, schema_ids):
        """Get the last active schema from a (list of) rule id(s)."""
        schemas = {}
        epoch = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
        date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        for schema_id in schema_ids:
            schema_name = root.find("rule[@id='" + schema_id + "']/name").text
            schema_date = root.find("rule[@id='" + schema_id + "']/modified_date").text
            # Python 3.6 fix (%z %Z issue)
            corrected = re.sub(
                r"([-+]\d{2}):(\d{2})(?:(\d{2}))?$", r"\1\2\3", schema_date,
            )
            schema_time = datetime.datetime.strptime(corrected, date_format)
            schemas[schema_name] = (schema_time - epoch).total_seconds()
        last_modified = sorted(schemas.items(), key=lambda kv: kv[1])[-1][0]
        return last_modified


class AnnaException(Exception):
    """Define Exceptions."""

    def __init__(self, arg1, arg2=None):
        """Set the base exception for interaction with the Anna gateway."""
        self.arg1 = arg1
        self.arg2 = arg2
        super(AnnaException, self).__init__(arg1)


class RuleIdNotFoundException(AnnaException):
    """Raise an exception for when the rule id is not found in the direct objects."""

    pass


class CouldNotSetPresetException(AnnaException):
    """Raise an exception for when the preset can not be set."""

    pass


class CouldNotSetTemperatureException(AnnaException):
    """Raise an exception for when the temperature could not be set."""

    pass
