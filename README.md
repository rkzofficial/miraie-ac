# MirAIe API for Python

### Installation

```
pip install miraie-ac
```

### Get started

```Python
import asyncio
from miraie_ac import MirAIeHub, MirAIeBroker

async def setup():
  # Instantiate a MirAIeHub object
  broker = MirAIeBroker()

  # Instantiate a MirAIeHub object
  hub = MirAIeHub()

  # Intialize the hub (+91xxxxxxxxxx, password, broker)
  await hub.init("<mobile>", "<password>", broker)
  
  # Display list of available devices
  print( hub.home.devices )
  
  # Wait till connection has been established with the broker
  async def waitForClient():
    while not hasattr(broker, 'client') or getattr(broker, 'client') is None:
      await asyncio.sleep(1)
  await waitForClient()

  # Now you can run any operation on the device(s)
  hub.home.devices[0].turn_off()
    
asyncio.run(setup())


```

### Logs can be enabled in Home Assistant as follows

```
logger:
  ...
  logs:
    ...
    custom_components.miraie: debug
    ...
```

### Notes
[List of panasonic ACs](https://www.panasonic.com/in/consumer/air-conditioners/split-ac/?browsing=params&sort=Featured&page=1)