import enum
import random
import logging
from typing import Optional

from .click_common import EnumType, command, format_output
from .device import Device
from .exceptions import DeviceException

_LOGGER = logging.getLogger(__name__)

MODEL_ACPARTNER_V1 = "lumi.acpartner.v1"
MODEL_ACPARTNER_V2 = "lumi.acpartner.v2"
MODEL_ACPARTNER_V3 = "lumi.acpartner.v3"
MODEL_ACPARTNER_MCN02 = "lumi.acpartner.mcn02"

MODELS_SUPPORTED = [MODEL_ACPARTNER_V1, MODEL_ACPARTNER_V2, MODEL_ACPARTNER_V3]


class AirConditioningCompanionException(DeviceException):
    pass


class OperationMode(enum.Enum):
    # 模式 M0 制冷 M1 制热 M2 自动 M3 送风 M4 除湿
    Cool = "M0"
    Heat = "M1"
    Auto = "M2"
    Ventilate = "M3"
    Dehumidify = "M4"


class FanSpeed(enum.Enum):
    # 风速 S0 自动 S1 低速 S2 中速 S3 高速
    Auto = "S0"
    Low = "S1"
    Medium = "S2"
    High = "S3"


class SwingMode(enum.Enum):
    # 扫风 D0 开启 D999 关闭
    On = "D0"
    Off = "D999"


class Power(enum.Enum):
    # P1 关机 P0 开机
    On = "P0"
    Off = "P1"


class AirConditioningCompanionStatus:
    """Container for status reports of the Xiaomi AC Companion."""

    def __init__(self, data):
        """
        Device model: lumi.acpartner.mcn02

        Response of "get_prop, params:["ac_state","load_power"]":
        ["P0_M0_T28_S1_D0",376.00]

        Example data payload:
        { 'state': ['P0', 'M0', 'T28', 'S1', 'D0'],
          'load_power': 21.00 }
        """
        self.data = data
        self.state = data["state"]
        self.load_power = data["load_power"]

    @property
    def load_power(self) -> int:
        """Current power load of the air conditioner."""
        return int(self.load_power)

    @property
    def power(self) -> str:
        """Current power state."""
        return "on" if int(self.state[0]) == Power.On.value else "off"

    @property
    def is_on(self) -> bool:
        """True if the device is turned on."""
        return self.power == "on"

    @property
    def target_temperature(self) -> Optional[int]:
        """Target temperature."""
        try:
            return int(self.state[2][1:])
        except TypeError:
            return None

    @property
    def swing_mode(self) -> Optional[SwingMode]:
        """Current swing mode."""
        try:
            mode = self.state[4]
            return SwingMode(mode)
        except TypeError:
            return None

    @property
    def fan_speed(self) -> Optional[FanSpeed]:
        """Current fan speed."""
        try:
            speed = self.state[3]
            return FanSpeed(speed)
        except TypeError:
            return None

    @property
    def mode(self) -> Optional[OperationMode]:
        """Current operation mode."""
        try:
            mode = self.state[1]
            return OperationMode(mode)
        except TypeError:
            return None

    def __repr__(self) -> str:
        s = (
            "<AirConditioningCompanionStatus "
            "power=%s, "
            "load_power=%s, "
            "target_temperature=%s, "
            "swing_mode=%s, "
            "fan_speed=%s, "
            "mode=%s>"
            % (
                self.power,
                self.load_power,
                self.target_temperature,
                self.swing_mode,
                self.fan_speed,
                self.mode,
            )
        )
        return s

    def __json__(self):
        return self.data


class AirConditioningCompanionMcn02(Device):
    """Main class representing Xiaomi Air Conditioning Companion V1 and V2."""

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = random.randint(0, 999),
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_ACPARTNER_MCN02,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover)

        if model != MODEL_ACPARTNER_MCN02:
            _LOGGER.error(
                "Device model %s unsupported. Please use AirConditioningCompanion", model
            )

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Load power: {result.load_power}\n"
            "Air Condition model: {result.air_condition_model}\n"
            "Target temperature: {result.target_temperature} °C\n"
            "Swing mode: {result.swing_mode}\n"
            "Fan speed: {result.fan_speed}\n"
            "Mode: {result.mode}\n",
        )
    )
    def status(self) -> AirConditioningCompanionStatus:
        """Return device status."""
        data = self.send("get_prop", ["ac_state", "load_power"])
        return AirConditioningCompanionStatus({'state': data[0].split('_'), 'load_power': data[1]})

    @command(default_output=format_output("Powering the air condition on"))
    def on(self):
        """Turn the air condition on by infrared."""
        return self.send("set_power", ["on"])

    @command(default_output=format_output("Powering the air condition off"))
    def off(self):
        """Turn the air condition off by infrared."""
        return self.send("set_power", ["off"])
