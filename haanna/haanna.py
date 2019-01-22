"""
Plugwise Anna HomeAssistant component
"""
import requests
import xml.etree.cElementTree as Etree

USERNAME = ''
PASSWORD = ''
ANNA_ENDPOINT = ''
ANNA_PING_ENDPOINT = '/ping'
ANNA_DOMAIN_OBJECTS_ENDPOINT = '/core/domain_objects'
ANNA_LOCATIONS_ENDPOINT = '/core/locations'


class Haanna(object):

    def __init__(self, username, password, host):
        """Constructor for this class"""
        self.set_credentials(username, password)
        self.set_anna_endpoint('http://' + host)

    @staticmethod
    def ping_anna_thermostat():
        """Ping the thermostat to see if it's online"""
        r = requests.get(ANNA_ENDPOINT + ANNA_PING_ENDPOINT, auth=(USERNAME, PASSWORD), timeout=10)

        if r.status_code != 404:
            raise ConnectionError("Could not connect to the gateway.")

        return True

    @staticmethod
    def get_domain_objects():
        r = requests.get(ANNA_ENDPOINT + ANNA_DOMAIN_OBJECTS_ENDPOINT, auth=(USERNAME, PASSWORD), timeout=10)

        if r.status_code != requests.codes.ok:
            raise ConnectionError("Could not get the domain objects.")

        return Etree.fromstring(r.text)

    def get_presets(self, root):
        """Gets the presets from the thermostat"""
        rule_id = self.get_rule_id_by_name(root, 'Thermostat presets')

        if rule_id is None:
            raise RuleIdNotFoundException("Could not find the rule id.")

        presets = self.get_preset_dictionary(root, rule_id)
        return presets

    @staticmethod
    def set_preset(root, preset):
        """Sets the given preset on the thermostat"""
        location_id = root.find("appliance[type='thermostat']/location").attrib['id']

        locations_root = Etree.fromstring(
            requests.get(
                ANNA_ENDPOINT + ANNA_LOCATIONS_ENDPOINT,
                auth=(USERNAME, PASSWORD),
                timeout=10
            ).text
        )

        current_location = locations_root.find("location[@id='" + location_id + "']")
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        r = requests.put(
            ANNA_ENDPOINT + ANNA_LOCATIONS_ENDPOINT + ';id=' + location_id,
            auth=(USERNAME, PASSWORD),
            data='<locations>' +
                 '<location id="' + location_id + '">' +
                 '<name>' + location_name + '</name>' +
                 '<type>' + location_type + '</type>' +
                 '<preset>' + preset + '</preset>' +
                 '</location>' +
                 '</locations>',
            headers={'Content-Type': 'text/xml'},
            timeout=10
        )

        if r.status_code != requests.codes.ok:
            raise CouldNotSetPresetException("Could not set the given preset: " + r.text)

        return r.text

    @staticmethod
    def get_current_preset(root):
        """Gets the current active preset"""
        location_id = root.find("appliance[type='thermostat']/location").attrib['id']
        return root.find("location[@id='" + location_id + "']/preset").text

    def get_temperature(self, root):
        """Gets the temperature from the thermostat"""
        point_log_id = self.get_point_log_id(root, 'temperature')
        measurement = self.get_measurement_from_point_log(root, point_log_id)

        return float(measurement)

    def get_target_temperature(self, root):
        """Gets the target temperature from the thermostat"""
        target_temperature_log_id = self.get_point_log_id(root, 'thermostat')
        measurement = self.get_measurement_from_point_log(root, target_temperature_log_id)

        return float(measurement)

    def get_outdoor_temperature(self, root):
        """Gets the temperature from the thermostat"""
        outdoor_temperature_log_id = self.get_point_log_id(root, 'outdoor_temperature')
        measurement = self.get_measurement_from_point_log(root, outdoor_temperature_log_id)

        return float(measurement)

    @staticmethod
    def set_temperature(root, temperature):
        """Sends a set request to the temperature with the given temperature"""
        location_id = root.find("appliance[type='thermostat']/location").attrib['id']

        thermostat_functionality_id = root.find(
            "location[@id='" + location_id + "']/actuator_functionalities/thermostat_functionality"
        ).attrib['id']

        temperature = str(temperature)

        r = requests.put(
            ANNA_ENDPOINT +
            ANNA_LOCATIONS_ENDPOINT +
            ';id=' + location_id +
            '/thermostat;id=' + thermostat_functionality_id,
            auth=(USERNAME, PASSWORD),
            data='<thermostat_functionality><setpoint>' + temperature + '</setpoint></thermostat_functionality>',
            headers={'Content-Type': 'text/xml'},
            timeout=10
        )

        if r.status_code != requests.codes.ok:
            CouldNotSetTemperatureException("Could not set the temperature." + r.text)

        return r.text

    @staticmethod
    def set_credentials(username, password):
        """Sets the username and password variables"""
        global USERNAME
        global PASSWORD
        USERNAME = username
        PASSWORD = password

    @staticmethod
    def get_credentials():
        return {'username': USERNAME, 'password': PASSWORD}

    @staticmethod
    def set_anna_endpoint(endpoint):
        """Sets the endpoint where the Anna resides on the network"""
        global ANNA_ENDPOINT
        ANNA_ENDPOINT = endpoint

    @staticmethod
    def get_anna_endpoint():
        return ANNA_ENDPOINT

    @staticmethod
    def get_point_log_id(root, log_type):
        """Gets the point log ID based on log type"""
        return root.find("module/services/*[@log_type='" + log_type + "']/functionalities/point_log").attrib['id']

    @staticmethod
    def get_measurement_from_point_log(root, point_log_id):
        """Gets the measurement from a point log based on point log ID"""
        return root.find("*/logs/point_log[@id='" + point_log_id + "']/period/measurement").text

    @staticmethod
    def get_rule_id_by_name(root, rule_name):
        """Gets the rule ID based on name"""
        rules = root.findall("rule")
        for rule in rules:
            if rule.find("name").text == rule_name:
                return rule.attrib['id']

    @staticmethod
    def get_preset_dictionary(root, rule_id):
        """Gets the presets from a rule based on rule ID and returns a dictionary with all the key-value pairs"""
        preset_dictionary = {}
        directives = root.find("rule[@id='" + rule_id + "']/directives")
        for directive in directives:
            preset_dictionary[directive.attrib['preset']] = float(directive.find("then").attrib['setpoint'])
        return preset_dictionary


class AnnaException(Exception):
    def __init__(self, arg1, arg2=None):
        """Base exception for interaction with the Anna gateway"""
        self.arg1 = arg1
        self.arg2 = arg2
        super(AnnaException, self).__init__(arg1)


class RuleIdNotFoundException(AnnaException):
    """Raise an exception for when the rule id is not found in the direct objects"""
    pass


class CouldNotSetPresetException(AnnaException):
    """Raise an exception for when the preset can not be set"""
    pass


class CouldNotSetTemperatureException(AnnaException):
    """Raise an exception for when the temperature could not be set"""
    pass
