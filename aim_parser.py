# translated from https://github.com/UMN-Rocket-Team/WINGS/blob/main/src-tauri/src/communication_drivers/aim_parser.rs
# by ChatGPT
import struct
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

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
    structure_id: int
    name: str
    fields: list[str]


@dataclass
class Packet:
    structure: PacketStructure
    field_data: list[PacketFieldValue]

    @staticmethod
    def default(structure: PacketStructure, raw_values: list[Any]):
        return Packet(structure, [PacketFieldValue(v) for v in raw_values])


META = "Aim_Meta"
ACCEL_Z = "Aim_AccelZ"
PRESSURE = "Aim_Pressure"
COMP_BATT = "Aim_BatComp"
EJECT_BATT = "Aim_BatEject"
TEMP = "Aim_Temp"
LINE_A = "Aim_LineA"
LINE_B = "Aim_LineB"
LINE_C = "Aim_LineC"
LINE_D = "Aim_LineD"
ACCEL_XY = "Aim_AccelXY"
GYRO = "Aim_GyroXYZ"
MAG = "Aim_MagXYZ"
GPS = "Aim_GPSLLSOL"
RSSI = "Aim_RSSI"
STATUS = "Aim_Status"
IDENTIFIER = "Aim_Ident"
GPS_TIME = "Aim_GPSTime"
TIMESTAMP = "Aim_TimeStamp"
ORIENTATION = "Aim_Orientation"


# this can def be consolidated with the above consts
# probably with enums and aliases
@dataclass
class PacketIdlist:
    meta: int = 0
    accel_z: int = 1
    pressure: int = 2
    comp_batt: int = 3
    eject_batt: int = 4
    temp: int = 5
    line_a: int = 6
    line_b: int = 7
    line_c: int = 8
    line_d: int = 9
    accel_xy: int = 10
    gyro: int = 11
    mag: int = 12
    gps: int = 13
    rssi: int = 14
    status: int = 15
    identifier: int = 16
    gps_time: int = 17
    timestamp: int = 18
    orientation: int = 19

    def get(self, key: str) -> int:
        return getattr(self, key, -1)


delimiter_packet_length = {
    0x02: 2,  # Accel Z
    0x03: 3,  # Pressure
    0x04: 2,  # Comp Batt
    0x05: 2,  # Eject Batt
    0x06: 2,  # Temp
    0x0B: 4,  # Accel XY
    0x0C: 6,  # Gyro XYZ
    0x0F: 2,  # RSSI
    0x11: 6,  # Identifier
    0x15: 8,  # Orientation
}


# ============================================================
# AimParser
# ============================================================


class AimParser:
    def __init__(self):
        self._next_id = 0
        self.init_time = time.time()

        self.packet_types = PacketIdlist(
            meta=self.make_pkt_struct(META, ["System time", "RSSI", "SNR"]),
            accel_z=self.make_pkt_struct(ACCEL_Z, ["System time", "Delta time", "Z acceleration"]),
            pressure=self.make_pkt_struct(PRESSURE, ["System time", "Delta time", "Pressure(Pa)"]),
            comp_batt=self.make_pkt_struct(COMP_BATT, ["System time", "Delta time", "ADC(V)"]),
            eject_batt=self.make_pkt_struct(EJECT_BATT, ["System time", "Delta time", "ADC(V)"]),
            temp=self.make_pkt_struct(TEMP, ["System time", "Delta time", "Temperature"]),
            line_a=self.make_pkt_struct(
                LINE_A,
                ["System time", "Delta time", "ADC", "Is_On", "Is_Input"],
            ),
            line_b=self.make_pkt_struct(
                LINE_B,
                ["System time", "Delta time", "ADC", "Is_On", "Is_Input"],
            ),
            line_c=self.make_pkt_struct(
                LINE_C,
                ["System time", "Delta time", "ADC", "Is_On", "Is_Input"],
            ),
            line_d=self.make_pkt_struct(
                LINE_D,
                ["System time", "Delta time", "ADC", "Is_On", "Is_Input"],
            ),
            accel_xy=self.make_pkt_struct(ACCEL_XY, ["System time", "Delta time", "X acceleration", "Y acceleration"]),
            gyro=self.make_pkt_struct(GYRO, ["System time", "Delta time", "X rotation", "Y rotation", "Z rotation"]),
            mag=self.make_pkt_struct(MAG, ["System time", "Delta time", "X flux", "Y flux", "Z flux"]),
            gps=self.make_pkt_struct(GPS, ["System time", "Delta time", "Lat", "Long", "MSL(mm)", "lock", "sat_num"]),
            rssi=self.make_pkt_struct(RSSI, ["System time", "Delta time", "RSSI"]),
            status=self.make_pkt_struct(
                STATUS,
                [
                    "System time",
                    "Delta time",
                    "State",
                    "Line D on",
                    "Line C on",
                    "Line B on",
                    "Line A on",
                    "Line A continuity",
                    "Line B continuity",
                    "Line C continuity",
                    "Line D continuity",
                    "Line A input",
                    "Line B input",
                    "Line C input",
                    "Line D input",
                ],
            ),
            identifier=self.make_pkt_struct(IDENTIFIER, ["System time", "Delta time", "Identifier"]),
            gps_time=self.make_pkt_struct(
                GPS_TIME,
                ["System time", "Delta time", "iTOW", "GPS Week", "Valid time", "Valid leap secs", "leap secs"],
            ),
            timestamp=self.make_pkt_struct(TIMESTAMP, ["System time", "Delta time", "Timestamp"]),
            orientation=self.make_pkt_struct(
                ORIENTATION, ["System time", "Delta time", "Quat x", "Quat y", "Quat z", "Quat w"]
            ),
        )

    def make_pkt_struct(self, name: str, fields: list[str]) -> PacketStructure:
        structure_id = self._next_id
        self._next_id += 1
        return PacketStructure(structure_id, name, fields)

    # --------------------------------------------------------

    def parse_transmission(self, transmission: bytearray) -> list[Packet]:

        print(f"Begin parse transmission {transmission}")

        packets = []

        if len(transmission) <= 63:
            return packets

        time_received = (time.time() - self.init_time) * 1000

        length = transmission[1]
        rssi = struct.unpack(">h", transmission[2:4])[0]
        snr = transmission[4]

        packets.append(Packet.default(self.packet_types.meta, [time_received, float(rssi), float(snr)]))

        print("\n".join(map(repr, packets)))

        i = 3

        while i < length:
            print(f"Parsing at index {i} with first byte {transmission[i]} / {hex(transmission[i])}")
            i += 2

            delta_time = transmission[i]
            delimiter = transmission[i + 1]

            data = [time_received, time_received + float(delta_time)]

            # -----------------------------

            if delimiter == 0x02:  # Accel Z
                val = struct.unpack(">h", transmission[i + 2 : i + 4])[0] / 256.0
                data.append(val)
                packets.append(Packet.default(self.packet_types.accel_z, data))
                i += 2

            elif delimiter == 0x03:  # Pressure
                val = int.from_bytes(transmission[i + 2 : i + 5], "big")
                data.append(val)
                packets.append(Packet.default(self.packet_types.pressure, data))
                i += 3

            elif delimiter in (0x04, 0x05):  # Comp Batt or Eject Batt
                raw = struct.unpack(">H", transmission[i + 2 : i + 4])[0]
                val = (3.3 * raw) / (2**16)
                key = "comp_batt" if delimiter == 0x04 else "eject_batt"
                data.append(val)
                packets.append(Packet.default(self.packet_types.get(key), data))
                i += 2

            elif delimiter == 0x06:  # Temp
                raw = struct.unpack(">H", transmission[i + 2 : i + 4])[0]
                data.append(raw / 100.0)
                packets.append(Packet.default(self.packet_types.temp, data))
                i += 2

            elif delimiter in (0x07, 0x0A):
                print("woa custom lines")
                i += 2
                
            elif delimiter == 0x0B:  # Accel XY
                x = struct.unpack(">h", transmission[i + 2 : i + 4])[0] / 256.0
                y = struct.unpack(">h", transmission[i + 4 : i + 6])[0] / 256.0
                data.extend([x, y])
                packets.append(Packet.default(self.packet_types.accel_xy, data))
                i += 4

            elif delimiter == 0x0C:  # Gyro XYZ
                x = struct.unpack(">h", transmission[i + 2 : i + 4])[0] / 70.0
                y = struct.unpack(">h", transmission[i + 4 : i + 6])[0] / 70.0
                z = struct.unpack(">h", transmission[i + 6 : i + 8])[0] / 70.0
                data.extend([x, y, z])
                packets.append(Packet.default(self.packet_types.gyro, data))
                i += 6

            elif delimiter == 0x0D:
                x = struct.unpack(">h", transmission[i + 2 : i + 4])[0]
                y = struct.unpack(">h", transmission[i + 4 : i + 6])[0]
                z = struct.unpack(">h", transmission[i + 6 : i + 8])[0]

                data.extend([x, y, z])
                packets.append(Packet.default(self.packet_types.mag, data))
                
                i += 6

            elif delimiter == 0x0E:
                lat = struct.unpack(">i", transmission[i + 2 : i + 6])[0]
                lon = struct.unpack(">i", transmission[i + 6 : i + 10])[0]
                msl = struct.unpack(">i", transmission[i + 10 : i + 14])[0]
                lock = struct.unpack(">?", int.to_bytes(transmission[i + 14] & 0b00100000))
                sat_num = struct.unpack(">c", int.to_bytes(transmission[i + 14] & 0b00011111))

                data.extend([lat, lon, msl, lock, sat_num])
                

            elif delimiter == 0x0F:  # RSSI
                val = struct.unpack(">h", transmission[i + 2 : i + 4])[0]
                data.append(val)
                packets.append(Packet.default(self.packet_types.rssi, data))
                i += 2

            elif delimiter == 0x10:

                data.extend([
                struct.unpack(">c", int.to_bytes((transmission[i + 2] & 0b11110000) >> 4))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 2] & 0b00001000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 2] & 0b00000100))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 2] & 0b00000010))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 2] & 0b00000001))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b10000000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b01000000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00100000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00010000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00001000))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00000100))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00000010))[0],
                struct.unpack(">?", int.to_bytes(transmission[i + 3] & 0b00000001))[0]])
                packets.append(Packet.default(self.packet_types.status, data))
                i += 2

            elif delimiter == 0x11:  # Identifier
                identifier = transmission[i + 2 : i + 8].decode(errors="ignore")
                data.append(identifier)
                packets.append(Packet.default(self.packet_types.identifier, data))
                i += 6

            elif delimiter == 0x12:

                data.extend([
                    struct.unpack(">I", transmission[i + 2 : i + 6])[0],
                    struct.unpack(">H", transmission[i + 6 : i + 8])[0],
                    struct.unpack(">?", int.to_bytes(transmission[i + 8] & 0b10000000))[0],
                    struct.unpack(">?", int.to_bytes(transmission[i + 8] & 0b01000000))[0],
                    struct.unpack(">c", int.to_bytes(transmission[i + 8] & 0b00111111))[0]])
                packets.append(Packet.default(self.packet_types.gps_time, data))

            elif delimiter == 0x14:
                data.extend([struct.unpack(">I", transmission[i + 2 : i + 4])[0]])
                packets.append(Packet.default(self.packet_types.timestamp, data))
                i += 4

            elif delimiter == 0x15:  # Orientation
                x, y, z, w = struct.unpack(">hhhh", transmission[i + 2 : i + 10])
                data.extend([x, y, z, w])
                packets.append(Packet.default(self.packet_types.orientation, data))
                i += 8

            else:
                # raise ValueError(f"Unknown packet delimiter: {hex(delimiter)}")
                print("its a packet we don't know " + hex(delimiter))

        return packets
