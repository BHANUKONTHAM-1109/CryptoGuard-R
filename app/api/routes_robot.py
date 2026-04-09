"""
CryptoGuard-R - Robot Command API
"""

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel, Field

from app.robot.command_gateway import submit_command
from app.robot.simulator import get_simulator, ALLOWED_COMMANDS
from app.core.auth import verify_token

router = APIRouter(prefix="/api/robot", tags=["robot"])


class CommandRequest(BaseModel):
    """Request to execute a robot command."""

    command: str = Field(..., min_length=1, max_length=500)
    signature_b64: str = Field(..., min_length=1)
    source_context: str | None = Field(default=None, max_length=10000)


@router.get("/state")
def get_robot_state(operator_id: str = None):
    # Operator Revocation Check
    if operator_id:
        from app.database.store import is_operator_valid
        if not is_operator_valid(operator_id):
            raise HTTPException(status_code=401, detail="Access Revoked. Your biometric profile was explicitly terminated by the Cryptographic Admin.")

    """Get current robot simulator state."""
    sim = get_simulator()
    # Provide the allowed commands dynamically based on mode
    from app.robot.simulator import UAV_COMMANDS, ROVER_COMMANDS
    from app.database.store import get_isolation_status
    commands = list(UAV_COMMANDS) if sim.state.mode == "UAV" else list(ROVER_COMMANDS)
    return {"state": sim.get_state(), "allowed_commands": commands, "is_isolated": get_isolation_status()}

class RobotConfig(BaseModel):
    mode: str = Field(..., description="Currently supports ROVER or UAV")

@router.post("/config")
def config_robot(req: RobotConfig, user_id: str = Depends(verify_token)):
    sim = get_simulator()
    if req.mode not in ["ROVER", "UAV"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid mode")
    sim.set_mode(req.mode)
    return {"message": f"Switched to {req.mode} mode", "state": sim.get_state()}


@router.post("/command")
def execute_command(req: CommandRequest, user_id: str = Depends(verify_token)):
    """Submit a signed command for execution."""
    # user_id is the operator_id
    operator_id = "Operator-" + user_id
    # We will pass operator_id so it can be logged in the admin panel
    return submit_command(
        command=req.command,
        signature_b64=req.signature_b64,
        source_context=req.source_context,
        operator_id=operator_id
    )
