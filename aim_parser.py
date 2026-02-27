# translated from https://github.com/UMN-Rocket-Team/WINGS/blob/main/src-tauri/src/communication_drivers/aim_parser.rs
# by ChatGPT
import struct
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

# ============================================================
# Packet System
# ============================================================


class PacketFieldType(Enum):
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    I16 = "i16"
    F32 = "f32"
    F64 = "f64"
    STRING = "string"


@dataclass
class PacketFieldValue:
    value: Any

    def __float__(self):
        return float(self.value)


@dataclass
class PacketStructure:
    name: str
    fields: List[str]


@dataclass
class Packet:
    structure_id: int
    field_data: List[PacketFieldValue]

    @staticmethod
    def default(structure_id: int, raw_values: List[Any]):
        return Packet(structure_id, [PacketFieldValue(v) for v in raw_values])


class PacketStructureManager:
    def __init__(self):
        self.structures = {}
        self.next_id = 0

    def enforce_packet_fields(self, name: str, fields: List[str]) -> int:
        if name not in self.structures:
            self.structures[name] = PacketStructure(name, fields)
            self.next_id += 1
            return self.next_id
        else:
            return list(self.structures.keys()).index(name) + 1


# ============================================================
# AimParser
# ============================================================


class AimParser:

    def __init__(self, ps_manager: PacketStructureManager):
        self.init_time = time.time()

        self.packet_ids = {
            "meta": ps_manager.enforce_packet_fields("Aim_Meta", ["System time", "RSSI", "SNR"]),
            "accel_z": ps_manager.enforce_packet_fields("Aim_AccelZ", ["System time", "Delta time", "Z acceleration"]),
            "pressure": ps_manager.enforce_packet_fields("Aim_Pressure", ["System time", "Delta time", "Pressure(Pa)"]),
            "comp_batt": ps_manager.enforce_packet_fields("Aim_BatComp", ["System time", "Delta time", "ADC(V)"]),
            "eject_batt": ps_manager.enforce_packet_fields("Aim_BatEject", ["System time", "Delta time", "ADC(V)"]),
            "temp": ps_manager.enforce_packet_fields("Aim_Temp", ["System time", "Delta time", "Temperature"]),
            "accel_xy": ps_manager.enforce_packet_fields(
                "Aim_AccelXY", ["System time", "Delta time", "X acceleration", "Y acceleration"]
            ),
            "gyro": ps_manager.enforce_packet_fields(
                "Aim_GyroXYZ", ["System time", "Delta time", "X rotation", "Y rotation", "Z rotation"]
            ),
            "rssi": ps_manager.enforce_packet_fields("Aim_RSSI", ["System time", "Delta time", "RSSI"]),
            "identifier": ps_manager.enforce_packet_fields("Aim_Ident", ["System time", "Delta time", "Identifier"]),
            "orientation": ps_manager.enforce_packet_fields(
                "Aim_Orientation", ["System time", "Delta time", "X", "Y", "Z", "W"]
            ),
        }

    # --------------------------------------------------------

    def parse_transmission(self, transmission: bytes) -> List[Packet]:

        packets = []

        if len(transmission) <= 5:
            return packets

        time_received = (time.time() - self.init_time) * 1000

        length = transmission[1]
        rssi = struct.unpack(">h", transmission[2:4])[0]
        snr = transmission[4]

        packets.append(Packet.default(self.packet_ids["meta"], [time_received, float(rssi), float(snr)]))

        i = 3

        while i < length:

            delta_time = transmission[i]
            delimiter = transmission[i + 1]

            data = [time_received, time_received + float(delta_time)]

            i += 2

            # -----------------------------

            if delimiter == 0x02:
                val = struct.unpack(">h", transmission[i : i + 2])[0] / 256.0
                data.append(val)
                packets.append(Packet.default(self.packet_ids["accel_z"], data))
                i += 2

            elif delimiter == 0x03:
                val = int.from_bytes(transmission[i : i + 3], "big")
                data.append(val)
                packets.append(Packet.default(self.packet_ids["pressure"], data))
                i += 3

            elif delimiter in (0x04, 0x05):
                raw = struct.unpack(">H", transmission[i : i + 2])[0]
                val = (3.3 * raw) / (2**16)
                key = "comp_batt" if delimiter == 0x04 else "eject_batt"
                data.append(val)
                packets.append(Packet.default(self.packet_ids[key], data))
                i += 2

            elif delimiter == 0x06:
                raw = struct.unpack(">H", transmission[i : i + 2])[0]
                data.append(raw / 100.0)
                packets.append(Packet.default(self.packet_ids["temp"], data))
                i += 2

            elif delimiter == 0x0B:
                x = struct.unpack(">h", transmission[i : i + 2])[0] / 256.0
                y = struct.unpack(">h", transmission[i + 2 : i + 4])[0] / 256.0
                data.extend([x, y])
                packets.append(Packet.default(self.packet_ids["accel_xy"], data))
                i += 4

            elif delimiter == 0x0C:
                x = struct.unpack(">h", transmission[i : i + 2])[0] / 70.0
                y = struct.unpack(">h", transmission[i + 2 : i + 4])[0] / 70.0
                z = struct.unpack(">h", transmission[i + 4 : i + 6])[0] / 70.0
                data.extend([x, y, z])
                packets.append(Packet.default(self.packet_ids["gyro"], data))
                i += 6

            elif delimiter == 0x0F:
                val = struct.unpack(">h", transmission[i : i + 2])[0]
                data.append(val)
                packets.append(Packet.default(self.packet_ids["rssi"], data))
                i += 2

            elif delimiter == 0x11:
                identifier = transmission[i : i + 6].decode(errors="ignore")
                data.append(identifier)
                packets.append(Packet.default(self.packet_ids["identifier"], data))
                i += 6

            elif delimiter == 0x15:
                x, y, z, w = struct.unpack(">hhhh", transmission[i : i + 8])
                data.extend([x, y, z, w])
                packets.append(Packet.default(self.packet_ids["orientation"], data))
                i += 8

            else:
                raise ValueError(f"Unknown packet delimiter: {hex(delimiter)}")

        return packets
