#!/usr/bin/env python3
"""Comprehensive regression test for /api/admin/* endpoints, RBAC, and disabling accounts."""

from __future__ import annotations

import os
import sys
import uuid
import atexit
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import app
from backend.app_data_store import AppDataStore
from backend.billing_store import BillingStore
from backend.config import Settings


def main() -> int:
    settings = Settings.from_env()
    client = TestClient(app, base_url="http://testserver")

    # 1. Setup admin user and regular user
    admin_uid = f"admin-test-{uuid.uuid4().hex}"
    service = importlib.import_module("backend.app")
    original_hard_users = service.settings.billing_hard_user_ids
    object.__setattr__(service.settings, "billing_hard_user_ids", original_hard_users | {admin_uid})

    admin_email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    user_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    password = "Password123456!"

    # Register admin
    app_data_store = AppDataStore(settings.database_url)
    billing_store = BillingStore(
        settings.database_url,
        enforcement_mode=settings.billing_enforcement_mode,
        hard_user_ids=settings.billing_hard_user_ids,
    )
    fixture_ids = {admin_uid}
    def cleanup() -> None:
        try:
            with app_data_store._connect() as conn:
                conn.execute("DELETE FROM app_users WHERE id = ANY(%s)", (list(fixture_ids),))
        finally:
            object.__setattr__(service.settings, "billing_hard_user_ids", original_hard_users)
    atexit.register(cleanup)

    with app_data_store._connect() as conn:
        # Insert admin user with matching admin_uid
        conn.execute(
            "INSERT INTO app_users (id, email, nickname, password_hash) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, password_hash = EXCLUDED.password_hash",
            (admin_uid, admin_email, "管理员", app_data_store._password_hash(password)),
        )

    # 2. Login as regular user
    reg_res = client.post("/api/auth/register", json={"email": user_email, "password": password, "nickname": "普通用户"})
    assert reg_res.status_code == 200, f"Register failed: {reg_res.text}"
    user_data = reg_res.json()
    user_id = user_data["id"]
    fixture_ids.add(user_id)
    assert user_data.get("is_admin") is False or user_data.get("is_admin") is None

    # Verify regular user gets 403 on /api/admin/*
    for endpoint in [
        "/api/admin/monitoring/summary",
        "/api/admin/costs",
        "/api/admin/transactions",
        "/api/admin/users",
        f"/api/admin/users/{user_id}",
    ]:
        res = client.get(endpoint)
        assert res.status_code == 403, f"Expected 403 for regular user on {endpoint}, got {res.status_code}"

    # 3. Login as Admin
    login_res = client.post("/api/auth/login", json={"email": admin_email, "password": password})
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    admin_data = login_res.json()
    assert admin_data.get("is_admin") is True, f"Admin user should have is_admin=True: {admin_data}"

    # 4. Test Monitoring Summary API
    mon_res = client.get("/api/admin/monitoring/summary?hours=24&bucket=hour")
    assert mon_res.status_code == 200, f"Monitoring summary 24h failed: {mon_res.text}"
    mon_data = mon_res.json()
    assert "series" in mon_data, "Missing series in monitoring summary"
    assert "models" in mon_data, "Missing models in monitoring summary"
    assert len(mon_data["series"]) >= 24, f"Expected >= 24 series points, got {len(mon_data['series'])}"

    mon_7d_res = client.get("/api/admin/monitoring/summary?hours=168&bucket=day")
    assert mon_7d_res.status_code == 200, f"Monitoring summary 7d failed: {mon_7d_res.text}"
    mon_7d_data = mon_7d_res.json()
    assert len(mon_7d_data["series"]) >= 7, f"Expected >= 7 series points, got {len(mon_7d_data['series'])}"

    # 5. Test Costs API
    cost_res = client.get("/api/admin/costs?hours=24")
    assert cost_res.status_code == 200, f"Costs API failed: {cost_res.text}"
    cost_data = cost_res.json()
    assert "totals" in cost_data
    assert "users" in cost_data

    # 6. Test Transactions API
    tx_res = client.get("/api/admin/transactions?page=1&limit=20")
    assert tx_res.status_code == 200, f"Transactions API failed: {tx_res.text}"
    tx_data = tx_res.json()
    assert "items" in tx_data
    assert "total" in tx_data

    # 7. Test Users API
    users_res = client.get("/api/admin/users?page=1&limit=20")
    assert users_res.status_code == 200, f"Users API failed: {users_res.text}"
    users_data = users_res.json()
    assert "users" in users_data
    assert any(u["id"] == user_id for u in users_data["users"])

    # Test User Detail API
    u_detail_res = client.get(f"/api/admin/users/{user_id}")
    assert u_detail_res.status_code == 200, f"User detail failed: {u_detail_res.text}"
    u_detail = u_detail_res.json()
    assert u_detail["email"] == user_email
    assert "stats_7d" in u_detail

    # Test User Profile Patch API (admin note & nickname)
    patch_res = client.patch(f"/api/admin/users/{user_id}/profile", json={"nickname": "测试改名", "admin_note": "测试备注"})
    assert patch_res.status_code == 200, f"User patch failed: {patch_res.text}"
    assert patch_res.json()["nickname"] == "测试改名"
    assert patch_res.json()["admin_note"] == "测试备注"

    # 8. Test Disable / Enable User
    # Admin cannot disable self
    self_dis_res = client.post(f"/api/admin/users/{admin_uid}/disable")
    assert self_dis_res.status_code == 400, "Admin should not be able to disable self"

    # Disable regular user
    dis_res = client.post(f"/api/admin/users/{user_id}/disable")
    assert dis_res.status_code == 200, f"Disable user failed: {dis_res.text}"
    assert dis_res.json()["status"] == "disabled"

    # Re-enable regular user
    en_res = client.post(f"/api/admin/users/{user_id}/enable")
    assert en_res.status_code == 200, f"Enable user failed: {en_res.text}"
    assert en_res.json()["status"] == "active"

    # 9. Test Conversations & Messages
    convs_res = client.get(f"/api/admin/users/{user_id}/conversations")
    assert convs_res.status_code == 200, f"Conversations failed: {convs_res.text}"

    print("All backend admin tests passed successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
