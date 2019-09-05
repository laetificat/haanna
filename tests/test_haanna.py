import time
import unittest
import xml.etree.cElementTree as Et
import os

from haanna import Haanna


class TestHaannaMethods(unittest.TestCase):

    def setUp(self):
        self.haanna = Haanna(
            os.environ.get('ANNA_USERNAME', 'smile'), 
            os.environ.get('ANNA_PASSWORD', 'short_id'),
            os.environ.get('ANNA_IP', 'ip_address'),
            os.environ.get('ANNA_PORT', 80)
            )

    def test_ping_anna_thermostat(self):
        """Ping the thermostst"""
        self.assertTrue(self.haanna.ping_anna_thermostat())

    def test_get_domain_objects(self):
        """Get the domain objects"""
        self.assertTrue(len(Et.tostring(self.haanna.get_domain_objects(), encoding='utf8', method='xml')) > 0)
        time.sleep(3)

    def test_get_presets(self):
        """Get the available presets"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertTrue(len(self.haanna.get_presets(domain_objects)) > 0)
        time.sleep(3)

    def test_set_preset(self):
        """Set preset to 'Away'"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertTrue(len(self.haanna.set_preset(domain_objects, 'away')) > 0)
        self.haanna.set_preset(domain_objects, 'home')
        time.sleep(3)

    def test_get_current_preset(self):
        """Get the current active preset"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertTrue(len(self.haanna.get_current_preset(domain_objects)) > 0)
        time.sleep(3)

    def test_get_current_temperature(self):
        """Get the current room temperature"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertIsInstance(self.haanna.get_current_temperature(domain_objects), float)
        time.sleep(3)

    def test_get_target_temperature(self):
        """Get the target temperature"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertIsInstance(self.haanna.get_target_temperature(domain_objects), float)
        time.sleep(3)
        
    def test_get_thermostat_temperature(self):
        """Get the target temperature"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertIsInstance(self.haanna.get_thermostat_temperature(domain_objects), float)
        time.sleep(3)

    def test_get_outdoor_temperature(self):
        """Get the outdoor temperature"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertIsInstance(self.haanna.get_outdoor_temperature(domain_objects), float)
        time.sleep(3)

    def test_set_temperature(self):
        """Set a new target temperature"""
        domain_objects = self.haanna.get_domain_objects()
        self.haanna.set_temperature(domain_objects, 22.00)
        domain_objects = self.haanna.get_domain_objects()
        self.assertEqual(22.00, self.haanna.get_target_temperature(domain_objects))
        time.sleep(3)

    def test_set_credentials(self):
        """Sets the credentials used to connect to the gateway"""
        self.haanna.set_credentials('username', 'password')
        self.assertEqual({'username': 'username', 'password': 'password'}, self.haanna.get_credentials())

    def test_set_anna_endpoint(self):
        """Sets the endpoint to connect to"""
        self.haanna.set_anna_endpoint('http://example.com')
        self.assertEqual('http://example.com', self.haanna.get_anna_endpoint())

    def test_get_point_log_id(self):
        """Gets the point log id by log type"""
        domain_objects = self.haanna.get_domain_objects()
        self.assertTrue(len(self.haanna.get_point_log_id(domain_objects, 'temperature')) > 0)
        time.sleep(3)

    def test_get_measurement_from_point_log(self):
        """Gets the measurement from the given point log"""
        domain_objects = self.haanna.get_domain_objects()
        temperature_point_log_id = self.haanna.get_point_log_id(domain_objects, 'temperature')
        self.assertTrue(float(self.haanna.get_measurement_from_point_log(domain_objects, temperature_point_log_id)) > 0)
        time.sleep(3)

    def test_get_rule_id_by_name(self):
        """Gets the rule id based on rule name"""
        domain_objects = self.haanna.get_domain_objects()
        if not self.haanna.is_legacy_anna(domain_objects):  # only test when it is not a legacy model
            self.assertTrue(len(self.haanna.get_rule_id_by_name(domain_objects, 'Thermostat presets')) > 0)
        time.sleep(3)

    def test_get_preset_dictionary(self):
        """Gets the available presets based on rule name"""
        domain_objects = self.haanna.get_domain_objects()
        if not self.haanna.is_legacy_anna(domain_objects):  # only test when it is not a legacy model
            rule_id = self.haanna.get_rule_id_by_name(domain_objects, 'Thermostat presets')
            self.assertTrue(len(self.haanna.get_preset_dictionary(domain_objects, rule_id)) > 0)
        time.sleep(3)

    def test_get_heating_status(self):
        """Gets the heating status - Hard to reproduce in a test; only verify the code does not raise an exception"""
        domain_objects = self.haanna.get_domain_objects()
        try:
            self.haanna.get_heating_status(domain_objects)
        except:
            assert False, "Unexpected exception"
    
    def test_get_domestic_hot_water_status(self):
        """Gets the domestic hot water status - Hard to reproduce in a test; only verify the code does not raise an exception"""
        domain_objects = self.haanna.get_domain_objects()
        try:
            self.haanna.get_domestic_hot_water_status(domain_objects)
        except:
            assert False, "Unexpected exception"

    def test_get_mode(self):
        """Gets the mode - Hard to reproduce in a test; only verify the code does not raise an exception"""
        domain_objects = self.haanna.get_domain_objects()
        try:
            self.haanna.get_mode(domain_objects)
        except:
            assert False, "Unexpected exception"

