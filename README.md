# MirAIe API for Python

### Installation

```
pip install miraie-ac
```

### Get started

```Python
from miraie-ac import MirAIeHub, MirAIeBroker

# Instantiate a MirAIeHub object
broker = MirAIeBroker()

# Instantiate a MirAIeHub object
hub = MirAIeHub()

# Intialize the hub (+91xxxxxxxxxx, password, broker)
hub.init(mobile, password, broker)
```

### Logs can be enabled in Home Assistant as follows

```
logger:
  ...
  logs:
    ...
    homeassistant.components.miraie: debug
    ...
```
