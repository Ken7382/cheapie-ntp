# Raspberry Pi Zero W Stratum 2 NTP Server & Triple 7-Segment Clock aka "cheapie-ntp"

<img width="2637" height="1067" alt="cheapie-ntp" src="https://github.com/user-attachments/assets/e11ee2d2-b783-46c9-a975-1789488b2f2d" />


I had AI (Gemini) help me build this - it's a simple NTP server running on a Raspberry Pi Zero W using a PoE adapter (though it's not required, that's just how I did it for power and low latency) with three TM1637 clock modules attached. The first one is obviously the hours/minutes, second display is seconds and whether it's AM or PM, third is the data (MM/DD format.) If you'd like to fork this or modify it for your own use (i.e. 24 hr format, etc.) feel free to! I've uploaded the simple stupid display box I designed and 3d printed (though I'm sure it could use some improvement as well.) You wind up with a nice simple little box for fairly cheap (hence the name) as the TM1637 modules can be had off Amazon in a pack of 5 for under $20. The PoE adapter I used is the UCTRONICS for Raspberry Pi Zero's on Amazon, around $20 at the time I wrote this.

Inspired by Jeff Geerling's awesome NTP time server setup, I wanted a cool 7-segment clock in my data closet but didn't want to spend the crazy amount of money for the fancy clock (and have to build an NTP server on top of it.) This whole unit can be made for under $100 (including the Pi Zero, cheaper if you already have one.) You'll need to solder a few connections for the displays but it's nothing crazy if you're already familiar with soldering small headers. I am no coder, so if you find a mistake don't be surprised. (It runs fine on my setup now, the clock displays work perfect and don't freeze, I've been running it for several months now.)

A dedicated, PoE-powered **Stratum 2 Network Time Protocol (NTP) server** built on a Raspberry Pi Zero W. It uses `chrony` to provide microsecond-accurate network time to local computers and IoT devices while driving **three 4-digit TM1637 7-segment LED displays** for a permanent readout of Hours/Minutes, Seconds + AM/PM, and Date.

## Hardware Requirements

* **Board:** Raspberry Pi Zero W (or Zero WH with pre-soldered headers)
* **Power/Network:** 2.4A PoE (Power over Ethernet) to Micro-USB splitter/adapter
* **Displays:** 3x 4-Digit TM1637 7-Segment LED Modules
* **Wiring:** Female header connectors, hookup wire, and heat-shrink tubing

## Wiring Diagram & Pinout

All three TM1637 modules share a parallel **5V (VCC)** and **Ground (GND)** connection, while each display uses dedicated GPIO pins for **Clock (CLK)** and **Data (DIO)**.

| Component | Module Pin | Pi GPIO (BCM) | Physical Pin |
| :--- | :--- | :--- | :--- |
| **All Displays (Parallel)** | VCC (5V)<br>GND | —<br>— | Pin 2<br>Pin 6 |
| **Display 1 (HH:MM)** | CLK<br>DIO | GPIO 23<br>GPIO 25 | Pin 16<br>Pin 22 |
| **Display 2 (SS A/P)** | CLK<br>DIO | GPIO 24<br>GPIO 22 | Pin 18<br>Pin 15 |
| **Display 3 (MM.DD)** | CLK<br>DIO | GPIO 27<br>GPIO 17 | Pin 13<br>Pin 11 |

---

## Step 1: Operating System Setup

Flash **Raspberry Pi OS Lite (Bookworm)** onto your MicroSD card using the Raspberry Pi Imager. *(Note: Bookworm is recommended over Trixie on the single-core Pi Zero W for faster boot times and lower CPU overhead).*

Update the OS and set your local timezone:
```bash
sudo apt update && sudo apt upgrade -y
sudo raspi-config
# Navigate to: Localization Options -> Timezone -> Select your region/city
```

---

## Step 2: Configure Chrony (Stratum 2 NTP Server)

1. Install `chrony`:
   ```bash
   sudo apt install chrony -y
   ```

2. Edit `/etc/chrony/chrony.conf`:
   ```bash
   sudo nano /etc/chrony/chrony.conf
   ```

3. Apply the following changes to prevent DHCP time loops (if broadcasting Option 42 on your network), allow local subnet queries, and enable instant time stepping on boot:
   ```text
   # 1. Comment out DHCP time sources so the Pi doesn't loop back to local DHCP servers
   # sourcedir /run/chrony-dhcp

   # 2. Allow all local subnets/VLANs to query this server (Keep UDP 123 blocked on WAN)
   allow all

   # 3. Continue serving local time even if internet connectivity drops temporarily
   local stratum 10

   # 4. Allow Chrony to immediately snap the clock forward on boot (Pi Zero lacks an RTC)
   makestep 1 -1
   ```

4. Restart Chrony and verify synchronization:
   ```bash
   sudo systemctl restart chrony
   chronyc tracking
   ```

---

## Step 3: Python Environment & Display Script

1. Create a project directory and set up a Python virtual environment:
   ```bash
   mkdir ~/ntp_clock && cd ~/ntp_clock
   sudo apt install python3-pip python3-venv -y
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the TM1637 driver library:
   ```bash
   pip install raspberrypi-tm1637
   ```

3. Save the `ntp_triple_clock.py` script (included in this repository) into `~/ntp_clock/ntp_triple_clock.py`.

---

## Step 4: Auto-Start Service (Systemd)

Create a `systemd` service so the displays start automatically at boot and recover if interrupted.

1. Run the following command to generate `/etc/systemd/system/ntpclock.service` using your current user paths:
   ```bash
   sudo bash -c "cat << 'EOF' > /etc/systemd/system/ntpclock.service
   [Unit]
   Description=NTP 3-Display 7-Segment Clock
   After=network.target chrony.service

   [Service]
   Type=simple
   User=\$USER
   WorkingDirectory=\$HOME/ntp_clock
   ExecStart=\(HOME/ntp_clock/venv/bin/python\)HOME/ntp_clock/ntp_triple_clock.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   EOF"
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ntpclock.service
   sudo systemctl start ntpclock.service
   ```

---

## Step 5: Network Distribution (DHCP & Firewall)

* **DHCP Option 42:** Add `dhcp-option=42,<PI_IP_ADDRESS>` to your DHCP server (e.g., `/etc/dnsmasq.d/99-ntp-dhcp.conf` on Pi-hole, or under Advanced DHCP Options in TP-Link Omada / UniFi).
* **Policy Routing (Optional):** For IoT devices that ignore DHCP Option 42 and query hardcoded public NTP servers, create a policy route on your router to intercept outbound **UDP Port 123** traffic and redirect it to `<PI_IP_ADDRESS>`.
