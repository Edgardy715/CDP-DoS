![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# CDP DoS Flood Attack

> **Autor:** Edgardy Olivero | **Matrícula:** 20250704
> **Laboratorio:** EGALDITO\_LAB | **Herramienta:** Python 3 + Scapy
> **Repositorio:** [github.com/Edgardy715/CDP-DoS](https://github.com/Edgardy715/CDP-DoS)

---

## 📋 Objetivo del Laboratorio

Demostrar cómo un atacante puede agotar los recursos de CPU y memoria de switches Cisco mediante la inundación masiva del protocolo CDP (Cisco Discovery Protocol), causando una condición de Denegación de Servicio (DoS) sin necesidad de credenciales ni acceso previo al dispositivo.

CDP opera sobre la multicast de capa 2 `01:00:0C:CC:CC:CC`, lo que significa que cualquier equipo conectado al mismo dominio L2 puede generar y recibir tráfico CDP sin autenticación. Este ataque no requiere subinterfaz VLAN ya que actúa directamente sobre la interfaz física `eth0` en la capa 2 nativa.

---

## 🎯 Objetivo del Script

Generar y transmitir paquetes CDP sintéticos a alta velocidad hacia la dirección multicast `01:00:0c:cc:cc:cc`, utilizando MACs de origen y Device-IDs únicos y aleatorios en cada iteración. El script fuerza al switch víctima a almacenar miles de entradas CDP en su tabla de vecinos hasta saturar la memoria disponible y elevar el uso de CPU.

---

## 📁 Estructura del Repositorio

```text
CDP-DoS/
├── Script/
│   └── cdp-DoS.py                        ← Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-CDP-DoS.ios            ← Comandos de contramedida (Cisco IOS)
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

## ⚙️ Parámetros del Script

| Variable | Valor | Descripción |
|---|---|---|
| `IFACE` | `eth0` | Interfaz física directa (sin subinterfaz). CDP opera en capa 2 nativa. |
| `INTERVALO` | `0.01` | Segundos entre paquetes (~100 pkt/s). |
| `dst` | `01:00:0c:cc:cc:cc` | Dirección multicast estándar de CDP. |
| `LLC dsap/ssap` | `0xAA` | Encapsulación SNAP requerida por CDP. |
| `SNAP OUI` | `0x00000C` | OUI de Cisco. |
| `SNAP code` | `0x2000` | Protocol ID de CDP. |
| `rand_mac()` | `02:xx:xx:xx:xx:xx` | MAC origen aleatoria por iteración. |

> **Nota:** A diferencia de los ataques DHCP y ARP de este laboratorio (que usan `eth0.10`), CDP es un protocolo de capa 2 puro que no viaja dentro de VLANs etiquetadas. Por eso se usa `eth0` directamente.

---

## 🛠️ Requisitos

```bash
# Sistema operativo
Kali Linux o cualquier distribución Linux con acceso root

# Dependencia Python
pip install scapy

# Verificar que la interfaz esté activa y conectada al switch
ip link show eth0

# Ejecutar
sudo python3 Script/cdp-DoS.py
```

---

## 🔍 Funcionamiento del Script

### Flujo de ejecución

```text
1. Verifica ejecución como root.
2. Bucle infinito hasta Ctrl+C.
3. En cada iteración:
   a. Genera una MAC origen aleatoria.
   b. Construye un paquete CDP multicapa (Ether / LLC / SNAP / CDPv2).
   c. Envía el frame con sendp() hacia 01:00:0c:cc:cc:cc.
   d. Incrementa el contador de paquetes.
   e. Imprime paquetes/segundo en tiempo real.
4. Ctrl+C → muestra el total enviado.
```

### Estructura del paquete generado

```text
[Ether]   src=MAC_aleatoria   dst=01:00:0c:cc:cc:cc
  [LLC]   dsap=0xAA  ssap=0xAA  ctrl=0x03
    [SNAP]  OUI=0x00000C  code=0x2000
      [CDPv2_HDR]
        [CDPMsgDeviceID]        val="device-{mac}"
        [CDPMsgPortID]          iface="GigabitEthernet0/0"
        [CDPMsgCapabilities]
        [CDPMsgPlatform]        val="cisco WS-C2960"
        [CDPMsgSoftwareVersion] val="Cisco IOS 15.2"
```

### Verificación en el switch durante el ataque

```cisco
SW2# show cdp neighbors
SW2# show cdp neighbors detail | count Device ID
SW2# show processes cpu sorted | head
```

> **Éxito confirmado:** la tabla CDP crece de forma anormal y el uso de CPU del switch aumenta significativamente.

---

## 🌐 Documentación de la Red

### Topología del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |◄──────►|  GNS3 vIOS-L2       |◄──────►|  GNS3 vIOS-L2       |
|     eth0         | Gi0/1  | VTP Client          | Gi0/0  | VTP Server          |
| 0c:bf:c5:c2:00:00|        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000      |
+------------------+        +---------------------+        +---------------------+
                                                                    | Gi0/1
                                                         +---------------------+
                                                         |         R1          |
                                                         |  192.168.10.1/24    |
                                                         +---------------------+
```

> Topología completa disponible en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Máscara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | `eth0` | 1 (nativa) | dinámica | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1, 10 | — | `0cb5.a4d7.0000` | VTP Server / Root Bridge |
| SW2 | Gi0/1 (acceso) | 1, 10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP Server |

```text
VTP Domain  : EGALDITO_LAB
SW1         : VTP Server | STP Root Bridge | Priority 32769 | MAC 0cb5.a4d7.0000
SW2         : VTP Client
VLAN 10     : RED_LOCAL — 192.168.10.0/24
```
---

## 🛡️ Contramedidas

El archivo de mitigación está en `Mitigacion/Mitigacion-CDP-DoS.ios`.

### 1. Deshabilitar CDP globalmente (recomendado si no se usa)

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

### Verificación

```cisco
SW2# show cdp
% CDP is not enabled
```

> `no cdp run` desactiva CDP en todo el switch. `no cdp enable` lo desactiva por interfaz, permitiendo mantener CDP activo en otros puertos donde sí sea necesario (por ejemplo, hacia otros switches Cisco).

---

## 🎬 Video Demostrativo

**Lista de reproducción EGALDITO\_LAB — Layer 2 Network Attacks:**
[https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j](https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j)

**Video de este ataque:**
[https://youtu.be/7fxeLDbxr44](https://youtu.be/7fxeLDbxr44)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*
*Autor: Edgardy Olivero | 20250704 | EGALDITO\_LAB*
