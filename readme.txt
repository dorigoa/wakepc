Install pip packages as shown in requirements.txt
Create a net conn 192.168.40.1/24 that can be used to wakeup the pc on 192.168.40.2/24
Copy wakepc.service in the proper location as shown in the head of the script itself
Create tailscale routing for this service:
	tailscale serve --https=8443 --bg http://127.0.0.1:9000

Ethernet card must have the Wakg flag on "`g`":
```bash
$ sudo ethtool enp38s0|grep Wake
	Supports Wake-on: pumbg
	Wake-on: g
```

If not, do this:
```bash
$ sudo ethtool -s enp38s0 wol g
```

Then reboot entering the BIOS and set Wake on LAN / Wake on PCI-E / Power On By PCI-E (PSI-E must be accepted as source of signal of wake up).
