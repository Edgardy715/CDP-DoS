![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# CDP DoS Flood Attack

> **Autor:** Edgardy Olivero | **Matricula:** 20250704  
> **Laboratorio:** EGALDITO_LAB | **Herramienta:** Python 3 + Scapy  
> **Repositorio:** [github.com/Edgardy715/CDP-DoS](https://github.com/Edgardy715/CDP-DoS)

---

## Objetivo del Laboratorio

Demostrar como un atacante puede agotar los recursos de CPU y memoria de switches Cisco mediante la inundacion masiva del protocolo CDP (Cisco Discovery Protocol), causando una condicion de Denegacion de Servicio (DoS) sin necesidad de credenciales ni acceso previo al dispositivo. CDP usa la multicast de capa 2 `01:00:0C:CC:CC:CC`, por lo que cualquier equipo en el mismo dominio L2 puede recibir y generar trafico CDP [web:59][web:62][web:64][web:68].

## Objetivo del Script

Generar y transmitir paquetes CDP sinteticos a alta velocidad hacia la direccion multicast `01:00:0c:cc:cc:cc`, utilizando MACs de origen y Device-IDs unicos y aleatorios en cada iteracion. El script fuerza al switch victima a almacenar miles de entradas CDP en su tabla de vecinos hasta saturar la memoria disponible y elevar el uso de CPU [web:59][web:64][web:65].

---

## Estructura del Repositorio

```text
CDP-DoS/
├── Script/
│   └── cdp-DoS.py                        <- Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-CDP-DoS.ios            <- Comandos de contramedida (Cisco IOS)
├── Conf-Topologia/
│   └── scripts_bases_configs/
│       ├── R1.ios
│       ├── SW1-VTPSERVER.ios
│       └── SW2.ios
├── Topologia/
│   └── Topologia.png
└── README.md
```

---

## Parametros del Script

| Variable | Valor | Descripcion |
|---|---|---|
| `IFACE` | `eth0` | Interfaz del atacante. |
| `INTERVALO` | `0.01` | Segundos entre paquetes, equivalente a ~100 pkt/s. |
| `dst` | `01:00:0c:cc:cc:cc` | Multicast estandar de CDP. |
| `LLC dsap` | `0xAA` | DSAP/SSAP para encapsulacion SNAP. |
| `SNAP OUI` | `0x00000C` | OUI de Cisco. |
| `SNAP code` | `0x2000` | Protocol ID de CDP. |
| `rand_mac()` | `02:xx:xx:xx:xx:xx` | MAC origen aleatoria por iteracion. |

---

## Requisitos

```bash
# Sistema
Kali Linux o cualquier distro Linux con acceso root

# Dependencia Python
pip install scapy

# Scapy CDP contrib
from scapy.all import *
load_contrib("cdp")

# Verificar interfaz activa
ip link show eth0

# Ejecutar
sudo python3 Script/cdp-DoS.py
```

---

## Funcionamiento del Script

### Flujo de ejecucion

```text
1. Verifica ejecucion como root.
2. Bucle infinito hasta Ctrl+C.
3. En cada iteracion:
   a. Genera una MAC origen aleatoria.
   b. Construye un paquete CDP multicapa.
   c. Envia el frame con sendp() hacia 01:00:0c:cc:cc:cc.
   d. Incrementa el contador de paquetes.
   e. Imprime paquetes/segundo en tiempo real.
4. Ctrl+C -> muestra el total enviado.
```

### Estructura del paquete generado

```text
[Ether]  src=MAC_aleatoria  dst=01:00:0c:cc:cc:cc
  [LLC]  dsap=0xAA  ssap=0xAA  ctrl=0x03
    [SNAP]  OUI=0x00000C  code=0x2000
      [CDPv2_HDR]
        [CDPMsgDeviceID]       val="device-{mac}"
        [CDPMsgPortID]         iface="GigabitEthernet0/0"
        [CDPMsgCapabilities]
        [CDPMsgPlatform]       val="cisco WS-C2960"
        [CDPMsgSoftwareVersion] val="Cisco IOS 15.2"
```

### Verificacion en el switch durante el ataque

```cisco
SW2# show cdp neighbors
SW2# show cdp neighbors detail | count Device ID
SW2# show processes cpu sorted | head
```

> Exito confirmado: la tabla CDP crece de forma anormal y la CPU del switch aumenta de forma significativa.

---

## Documentacion de la Red

### Topologia del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |<------>|  GNS3 vIOS-L2       |<------>|  GNS3 vIOS-L2      |
|     eth0         |  Gi0/1 | VTP Client          |  Gi0/0 | VTP Server         |
| 0c:bf:c5:c2:0000 |        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000    |
+------------------+        +---------------------+        +---------------------+
                                                                   |  Gi0/1
                                                        +---------------------+
                                                        |         R1          |
                                                        |  192.168.10.1/24    |
                                                        +---------------------+
```

> Topologia completa en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Mascara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | eth0 | 1 | dinamica | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1,10 | — | `0cb5.a4d7.0000` | VTP Server / Root |
| SW2 | Gi0/0 (trunk) | 1,10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP |

```text
VTP Domain: EGALDITO_LAB | SW1: VTP Server | SW2: VTP Client
STP Root Bridge: SW1 | Priority: 32769 | MAC: 0cb5.a4d7.0000
VLAN 10: RED_LOCAL (192.168.10.0/24)
```

---

## Capturas de Pantalla

| Momento | Descripcion |
|---|---|
| Pre-ataque | `show cdp neighbors` muestra pocos vecinos legitimos. |
| Durante ataque | Contador de paquetes avanza ~100 pkt/s. |
| Impacto en switch | Tabla CDP desbordada y CPU elevada. |
| Post-mitigacion | `show cdp` muestra `% CDP is not enabled`. |

---

## Contramedidas

El archivo de mitigacion esta en `Mitigacion/Mitigacion-CDP-DoS.ios`.

### 1. Deshabilitar CDP globalmente

```cisco
en
conf term
no cdp run
do wr
```

### 2. Deshabilitar CDP solo en el puerto del atacante

```cisco
en
conf term
interface GigabitEthernet0/1
 no cdp enable
exit
do wr
```

### Verificacion

```cisco
SW2# show cdp
% CDP is not enabled
```

> CDP puede deshabilitarse globalmente con `no cdp run` o por interfaz con `no cdp enable`, que son las medidas clasicas para reducir la exposicion a ataques CDP [web:60][web:63][web:65].

---

## Video Demostrativo

**Lista de reproduccion EGALDITO_LAB:** [Layer 2 Network Attacks](https://www.youtube.com/@Edgardy715)

El video incluye:
- Topologia visible con nombre y matricula.
- Fecha y hora en pantalla.
- Camara y voz del autor.
- Demostracion del ataque en tiempo real.
- Aplicacion y verificacion de la contramedida.

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*  
*Autor: Edgardy Olivero | 20250704 | EGALDITO_LAB*
