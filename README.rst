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
  api = haanna.Haanna('smile', 'short_id', '192.168.1.60')

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

..

To do:
""""""
- Multiple thermostat support
- Set and get presets
- Optimize fetching of domain objects
- Add support for custom port mapping