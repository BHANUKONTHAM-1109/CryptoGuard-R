"""Tests for robot simulation and command gateway."""

import base64
import pytest
from pathlib import Path

sys_path = Path(__file__).resolve().parent.parent
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))


def test_command_rejected_unsigned():
    """Command without signature should be rejected."""
    from app.robot.command_gateway import submit_command
    r = submit_command("MOVE_FORWARD 5", signature_b64=None)
    assert r.get("code") == "MISSING_SIGNATURE"
    assert not r.get("success", True)


def test_command_rejected_invalid_signature():
    """Command with invalid signature should be rejected."""
    from app.robot.command_gateway import submit_command
    r = submit_command("MOVE_FORWARD 5", signature_b64=base64.b64encode(b"bad").decode())
    assert r.get("code") == "INVALID_SIGNATURE"


def test_command_accepted_signed():
    """Valid signed command should execute."""
    from app.crypto import get_or_create_rsa_keys, sign_string
    from app.robot.command_gateway import submit_command
    from app.robot.simulator import get_simulator
    priv_path = sys_path / "keys" / "rsa_private.pem"
    pub_path = sys_path / "keys" / "rsa_public.pem"
    priv, _ = get_or_create_rsa_keys(priv_path, pub_path)
    get_simulator().reset()
    cmd = "MOVE_FORWARD 2"
    sig = base64.b64encode(sign_string(cmd, priv)).decode()
    r = submit_command(cmd, signature_b64=sig)
    assert r.get("success")
    assert r.get("command") == "MOVE_FORWARD"
    assert r.get("state", {}).get("x") == 2.0


def test_unknown_command_rejected():
    """Unknown command should be rejected by simulator."""
    from app.crypto import get_or_create_rsa_keys, sign_string
    from app.robot.command_gateway import submit_command
    priv_path = sys_path / "keys" / "rsa_private.pem"
    pub_path = sys_path / "keys" / "rsa_public.pem"
    priv, _ = get_or_create_rsa_keys(priv_path, pub_path)
    cmd = "EXPLODE"
    sig = base64.b64encode(sign_string(cmd, priv)).decode()
    r = submit_command(cmd, signature_b64=sig)
    assert not r.get("success")
    assert "Unknown command" in r.get("message", "")


def test_replay_rejected():
    """Repeated identical signed command should be rejected (replay)."""
    from app.crypto import get_or_create_rsa_keys, sign_string
    from app.robot.command_gateway import submit_command
    from app.robot.simulator import get_simulator
    priv_path = sys_path / "keys" / "rsa_private.pem"
    pub_path = sys_path / "keys" / "rsa_public.pem"
    priv, _ = get_or_create_rsa_keys(priv_path, pub_path)
    get_simulator().reset()
    cmd = "STOP"
    sig = base64.b64encode(sign_string(cmd, priv)).decode()
    r1 = submit_command(cmd, signature_b64=sig)
    r2 = submit_command(cmd, signature_b64=sig)
    assert r1.get("success")
    assert r2.get("code") == "REPLAY_DETECTED"
