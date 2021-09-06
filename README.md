# ZeroTier_HA
Check your devices in your ZeroTier net and their states

This Home Assistant integration, expose all devices found in given ZeroTier network and shows:
- Status of device (connected or not)
- Local IP
- Remote IP
- Last connection time

in configuration.yaml insert:

	ZeroTier:
	  network: <ZeroTier network id>
	  token: <your ZeroTier API token>
