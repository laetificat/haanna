Haanna (HA Anna)
----------------
A Python API made for use in conjunction with the Home Assistant Anna component, but this API can also be used in other projects.

Installation
""""""""""""
.. code-block:: bash

  pip install haanna

..

Usage
"""""

.. code-block:: python3

  from haanna import haanna

  # Create the API
  api = haanna.Haanna('smile', 'short_id', '192.168.1.60', 80)

  # Fetch the domain objects
  domain_objects = api.get_domain_objects()

  # Set the temperature
  temperature = api.set_temperature(domain_objects, 22.50)
  print(temperature)

  # Get the temperature
  temperature = api.get_temperature(domain_objects)
  print(temperature)

  # Get the outdoor temperature
  temperature = api.get_outdoor_temperature(domain_objects)
  print(temperature)

  # Get the target temperature
  temperature = api.get_target_temperature(domain_objects)
  print(temperature)

  # Get the available presets
  presets = api.get_presets(domain_objects)
  print(presets)

  # Get the current active preset
  current_preset = api.get_current_preset(domain_objects)
  print(current_preset)

  # Set a preset
  preset = api.set_preset(domain_objects, 'away')
  print(preset)

  # Get operation mode (true = active schedule - false = no active schedules)
  # it 'walks' all schedules and sends true if one is active
  mode = api.get_mode(domain_objects)
  print(mode)

  # Get heating status (true = heating is on, flame on display)
  heating = api.get_heating_status(domain_objects)
  print(heating)

  # Get schemas or schedules available on the device.
  schemas = get_schema_names(domain_objects)
  print(schemas)

  # Sends a set request to the schema with the given name
  set_schema_state(domain_objects, schema=None, state)

  # Get active schema or determine last modified.
  schema = get_active_schema_name(domain_objects)
  print(schemas)

  # Gets the mode the thermostat is in (active schedule true or false)
  state = get_schema_state(domain_objects)
  print(state)
""""


To do:
""""""
- Optimize fetching of domain objects
- Add support for custom port mapping
