"""
Plugwise Anna HomeAssistant component
"""
import requests
import xml.etree.cElementTree as ET

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

        if self.ping_anna_thermostat() is False:
            raise ConnectionError("Could not connect to the gateway.")

    def ping_anna_thermostat(self):
        """Ping the thermostat to see if it's online"""
        r = requests.get(ANNA_ENDPOINT + ANNA_PING_ENDPOINT, auth=(USERNAME, PASSWORD))
        return r.status_code == 404

    def get_domain_objects(self):
        r = requests.get(ANNA_ENDPOINT + ANNA_DOMAIN_OBJECTS_ENDPOINT, auth=(USERNAME, PASSWORD))

        if r.status_code != requests.codes.ok:
            print("Could not get the domain objects.")
            print(r.status_code)
            print(r.text)
            return

        return ET.fromstring(r.text)

    def get_presets(self, root):
        """Gets the presets from the thermostat"""
        rule_id = self.get_rule_id_by_name(root, 'Thermostat presets')
        presets = self.get_preset_dictionary(root, rule_id)
        return presets

    def set_preset(self, root, preset):
        """Sets the given preset on the thermostat"""
        location_id = root.find("appliance[type='thermostat']/location").attrib['id']

        locations_root = ET.fromstring(requests.get(ANNA_ENDPOINT + ANNA_LOCATIONS_ENDPOINT, auth=(USERNAME, PASSWORD)).text)
        current_location = locations_root.find("location[@id='" + location_id + "']")
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        r = requests.put(
            ANNA_ENDPOINT + ANNA_LOCATIONS_ENDPOINT + ';id=' + location_id,
            auth=(USERNAME, PASSWORD),
            data='<locations><location id="' + location_id + '"><name>' + location_name + '</name><type>' + location_type + '</type><preset>' + preset + '</preset></location></locations>',
            headers={'Content-Type': 'text/xml'}
        )

        return r.status_code == 200

    def get_current_preset(self, root):
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

    def set_temperature(self, root, temperature):
        """Sends a set request to the temperature with the given temperature"""
        location_id = root.find("appliance[type='thermostat']/location").attrib['id']
        thermostat_functionality_id = root.find("location[@id='" + location_id + "']/actuator_functionalities/thermostat_functionality").attrib['id']
        temperature = str(temperature)

        r = requests.put(
            ANNA_ENDPOINT + ANNA_LOCATIONS_ENDPOINT + ';id=' + location_id + '/thermostat;id=' + thermostat_functionality_id,
            auth=(USERNAME, PASSWORD),
            data='<thermostat_functionality><setpoint>' + temperature + '</setpoint></thermostat_functionality>',
            headers={'Content-Type': 'text/xml'}
        )

        return r.status_code == 202

    def set_credentials(self, username, password):
        """Sets the username and password variables"""
        global USERNAME
        global PASSWORD
        USERNAME = username
        PASSWORD = password

    def set_anna_endpoint(self, endpoint):
        """Sets the endpoint where the Anna resides on the network"""
        global ANNA_ENDPOINT
        ANNA_ENDPOINT = endpoint

    def get_point_log_id(self, root, log_type):
        """Gets the point log ID based on log type"""
        return root.find("module/services/*[@log_type='" + log_type + "']/functionalities/point_log").attrib['id']

    def get_measurement_from_point_log(self, root, point_log_id):
        """Gets the measurement from a point log based on point log ID"""
        return root.find("*/logs/point_log[@id='" + point_log_id + "']/period/measurement").text

    def get_rule_id_by_name(self, root, rule_name):
        """Gets the rule ID based on name"""
        current_rule = root.find("rule")
        if current_rule.find("name").text == rule_name:
            return current_rule.attrib['id']

    def get_preset_dictionary(self, root, rule_id):
        """Gets the presets from a rule based on rule ID and returns a dictionary with all the key-value pairs"""
        preset_dictionary = {}
        directives = root.find("rule[@id='" + rule_id + "']/directives")
        for directive in directives:
            preset_dictionary[directive.attrib['preset']] = float(directive.find("then").attrib['setpoint'])
        return preset_dictionary
