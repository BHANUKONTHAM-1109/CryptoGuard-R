"""
CryptoGuard-R - Simulated Robot
Software simulation of a robotic system for testing. No physical hardware.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger("simulator")

# Shared base commands
BASE_COMMANDS = {"STOP"}
ROVER_COMMANDS = BASE_COMMANDS | {"MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT"}
UAV_COMMANDS = ROVER_COMMANDS | {"ASCEND", "DESCEND"}

ALLOWED_COMMANDS = UAV_COMMANDS # Superset for API info

@dataclass
class RobotState:
    """Current simulated robot state."""
    x: float
    y: float
    z: float  # Altitude/Height
    heading_deg: float  # 0=East, 90=North, 180=West, 270=South
    is_moving: bool
    mode: str = "ROVER" # 'ROVER' or 'UAV'
    last_command: str = "IDLE"


class RobotSimulator:
    """
    Simulated robot for CryptoGuard-R.
    Executes whitelisted commands and maintains state based on Mode.
    """

    def __init__(self) -> None:
        self.state = RobotState(x=0.0, y=0.0, z=0.0, heading_deg=0.0, is_moving=False)
        self._step_distance = 1.0
        self._turn_angle = 90.0
        self._alt_step = 10.0

    def set_mode(self, mode: str):
        if mode in ["ROVER", "UAV"]:
            self.state.mode = mode
            if mode == "ROVER":
                self.state.z = 0.0 # Rovers don't fly

    def _parse_command(self, raw: str) -> Tuple[str, float]:
        parts = raw.strip().upper().split()
        if not parts:
            return ("", 0.0)
        cmd = parts[0]
        arg = 1.0
        if len(parts) >= 2:
            try:
                arg = float(parts[1])
            except ValueError:
                arg = 1.0
        return (cmd, arg)

    def execute(self, command: str) -> Dict[str, Any]:
        """
        SECURITY: Only whitelisted mode-specific commands are executed.
        ENTERPRISE LOGIC: Actions are verified against physical operational boundaries.
        """
        cmd, arg = self._parse_command(command)
        
        valid_commands = UAV_COMMANDS if self.state.mode == "UAV" else ROVER_COMMANDS
        if cmd not in valid_commands:
            logger.warning("Rejected unknown/invalid command for mode %s: %s", self.state.mode, cmd)
            return {
                "success": False,
                "message": f"Command {cmd} not valid in {self.state.mode} mode.",
                "allowed": list(valid_commands),
                "state": self._state_dict(),
            }
            
        try:
            # Predict next state to perform boundary verification
            import copy
            next_state = copy.deepcopy(self.state)
            
            if cmd == "MOVE_FORWARD":
                next_state = self._predict_move(next_state, arg)
            elif cmd == "MOVE_BACKWARD":
                next_state = self._predict_move(next_state, -arg)
            elif cmd == "TURN_LEFT":
                next_state.heading_deg = (next_state.heading_deg + self._turn_angle * arg) % 360
            elif cmd == "TURN_RIGHT":
                next_state.heading_deg = (next_state.heading_deg - self._turn_angle * arg) % 360
            elif cmd == "ASCEND" and next_state.mode == "UAV":
                next_state.z += self._alt_step * arg
            elif cmd == "DESCEND" and next_state.mode == "UAV":
                next_state.z = max(0.0, next_state.z - self._alt_step * arg)
            elif cmd == "STOP":
                next_state.is_moving = False
                
            # Perform Enterprise Operational Boundary Checks
            if self.state.mode == "ROVER":
                if abs(next_state.x) > 50.0 or abs(next_state.y) > 50.0:
                    raise ValueError("Operation aborted. Rover exceeds 50m geofence matrix.")
            if self.state.mode == "UAV":
                if next_state.z > 200.0:
                    raise ValueError("Operation aborted. Drone exceeds FAA enterprise ceiling (200m).")
                if abs(next_state.x) > 500.0 or abs(next_state.y) > 500.0:
                    raise ValueError("Operation aborted. Drone exceeds 500m geofence.")

            # Apply state if verification passes
            self.state = next_state
            self.state.last_command = f"{cmd} {arg}"
                
            return {
                "success": True,
                "message": f"Executed {cmd} and verified within operational boundaries.",
                "command": cmd,
                "arg": arg,
                "state": self._state_dict(),
            }
        except Exception as e:
            logger.exception("Command execution failed or rejected: %s", cmd)
            return {
                "success": False,
                "message": str(e),
                "command": cmd,
                "state": self._state_dict(),
            }

    def _predict_move(self, state, distance: float):
        import math
        rad = math.radians(state.heading_deg)
        state.x += distance * self._step_distance * math.cos(rad)
        state.y += distance * self._step_distance * math.sin(rad)
        return state

    def _state_dict(self) -> Dict[str, Any]:
        return {
            "x": round(self.state.x, 2),
            "y": round(self.state.y, 2),
            "z": round(self.state.z, 2),
            "heading_deg": round(self.state.heading_deg, 2),
            "is_moving": self.state.is_moving,
            "mode": self.state.mode,
            "last_command": getattr(self.state, "last_command", "IDLE")
        }

    def get_state(self) -> Dict[str, Any]:
        return self._state_dict()

    def reset(self) -> Dict[str, Any]:
        self.state = RobotState(x=0.0, y=0.0, z=0.0, heading_deg=0.0, is_moving=False, last_command="IDLE")
        return self._state_dict()

_simulator: RobotSimulator | None = None

def get_simulator() -> RobotSimulator:
    global _simulator
    if _simulator is None:
        _simulator = RobotSimulator()
    return _simulator
