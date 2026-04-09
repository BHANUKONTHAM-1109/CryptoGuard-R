from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from app.database.store import (
    get_all_transactions, update_transaction_status, get_transaction,
    check_admin_credentials, change_admin_password,
    get_operators, remove_operator
)
from app.robot.simulator import get_simulator

router = APIRouter(prefix="/api/admin", tags=["admin"])

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminChangePasswordRequest(BaseModel):
    new_password: str

@router.post("/login")
def admin_login(data: AdminLoginRequest):
    if check_admin_credentials(data.username, data.password):
        return {"access_token": "admin_token", "message": "Admin Login Successful"}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")

@router.post("/change-password")
def change_password(data: AdminChangePasswordRequest):
    # In a real app we'd verify admin_token here
    change_admin_password(data.new_password)
    return {"message": "Admin password changed successfully"}

@router.get("/operators")
def list_operators():
    return {"operators": get_operators()}

@router.delete("/operators/{op_id}")
def delete_operator(op_id: str):
    if remove_operator(op_id):
        return {"message": f"Operator {op_id} revoked"}
    raise HTTPException(status_code=404, detail="Operator not found")

@router.get("/transactions")
def list_transactions():
    """List all transactions for the admin dashboard"""
    # Ideally should verify admin token here, but keeping it simple
    return {"transactions": get_all_transactions()}

@router.post("/transactions/{tx_id}/approve")
def approve_transaction(tx_id: str):
    tx = get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Transaction is not pending")
        
    update_transaction_status(tx_id, "APPROVED")
    
    # Execute the command
    sim = get_simulator()
    result = sim.execute(tx["command"])
    return {"message": "Transaction approved", "execution_result": result}
    
@router.post("/transactions/{tx_id}/reject")
def reject_transaction(tx_id: str):
    tx = get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Transaction is not pending")
        
    update_transaction_status(tx_id, "REJECTED")
    return {"message": "Transaction rejected"}

@router.post("/isolation/reset")
def reset_isolation():
    from app.database.store import set_isolation_status
    set_isolation_status(False)
    return {"message": "Self-Healing Network Isolation has been reset. Hardware uplink restored."}
