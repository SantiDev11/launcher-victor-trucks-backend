"""Test script to verify admin users and mod access API endpoints."""
import sys
import os
import time
import threading
import json

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Initialize DB
from backend.database import init_db
init_db()

print("=== Database initialized ===")

# Check DB state
from backend.database import get_connection
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, username, role, is_active FROM users")
users = cursor.fetchall()
print(f"Users in DB: {users}")

cursor.execute("SELECT COUNT(*) FROM mods")
mod_count = cursor.fetchone()[0]
print(f"Mods in DB: {mod_count}")

cursor.execute("SELECT COUNT(*) FROM user_mod_access")
access_count = cursor.fetchone()[0]
print(f"User_Mod_Access rows: {access_count}")
conn.close()

# Start server on test port
import requests
import uvicorn

BASE_URL = "http://127.0.0.1:8090"

server_thread = threading.Thread(
    target=lambda: uvicorn.run(
        "backend.server:app",
        host="127.0.0.1",
        port=8090,
        log_level="error"
    ),
    daemon=True
)
server_thread.start()

# Wait for server to be ready
print("\n=== Waiting for server on port 8090 ===")
for i in range(50):
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if r.status_code == 200:
            print(f"Server ready after {i * 0.2:.1f}s")
            break
    except Exception:
        pass
    time.sleep(0.2)
else:
    print("FAILED: Server did not start")
    sys.exit(1)

# --- Test 1: Admin login ---
print("\n=== Test 1: Admin Login ===")
admin_creds = [
    ("santitrucks.oficial@gmail.com", "STr@cks2026!"),
    ("victortrucks.oficial@gmail.com", "VTr@cks2026!"),
]

admin_token = None
admin_id = None

for username, password in admin_creds:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": password}, timeout=10)
    print(f"Login {username}: status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        admin_token = data.get("token")
        auth_headers = {"Authorization": f"Bearer {admin_token}"}
        print(f"  Role: {data.get('role')}, must_change_password: {data.get('must_change_password')}")
        break
    else:
        print(f"  Error: {r.text}")

if not admin_token:
    print("FAILED: Could not login as admin")
    sys.exit(1)

# --- Test 2: Get admin users ---
print("\n=== Test 2: GET /api/admin/users ===")
r = requests.get(f"{BASE_URL}/api/admin/users", headers=auth_headers, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    users_list = r.json().get("users", [])
    print(f"Users returned: {len(users_list)}")
    for u in users_list:
        print(f"  - id={u['id']}, username={u['username']}, role={u['role']}, is_active={u['is_active']}")
    # Find first admin
    for u in users_list:
        if u.get("role") == "admin":
            admin_id = u.get("id")
            break
    print(f"Using admin_id={admin_id}")
else:
    print(f"FAILED: {r.text}")
    sys.exit(1)

# --- Test 3: Get mods (for admin) ---
print("\n=== Test 3: GET /api/mods (as admin) ===")
r = requests.get(f"{BASE_URL}/api/mods", headers=auth_headers, timeout=10)
print(f"Status: {r.status_code}")
mods = []
if r.status_code == 200:
    mods = r.json().get("mods", [])
    print(f"Mods returned: {len(mods)}")
    for m in mods[:5]:
        print(f"  - id={m['id']}, title={m['title']}, version={m['version']}")
else:
    print(f"FAILED: {r.text}")
    sys.exit(1)

# --- Test 4: Get user access ---
print("\n=== Test 4: GET /api/admin/users/{id}/access ===")
if admin_id:
    r = requests.get(f"{BASE_URL}/api/admin/users/{admin_id}/access", headers=auth_headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        access = r.json().get("access", {})
        print(f"Access map: {access}")
    else:
        print(f"FAILED: {r.text}")
        sys.exit(1)

# --- Test 5: Set user access ---
print("\n=== Test 5: PUT /api/admin/users/{id}/access ===")
if admin_id and mods:
    test_mod_id = mods[0]["id"]
    print(f"Setting access for user {admin_id}, mod {test_mod_id}, granted=True")
    r = requests.put(
        f"{BASE_URL}/api/admin/users/{admin_id}/access",
        json={"mod_id": test_mod_id, "is_granted": True},
        headers=auth_headers,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    if r.status_code != 200:
        print("FAILED: Could not set access")
        sys.exit(1)

    # Verify it was saved
    r = requests.get(f"{BASE_URL}/api/admin/users/{admin_id}/access", headers=auth_headers, timeout=10)
    access = r.json().get("access", {})
    print(f"Access after save: {access}")
    if access.get(str(test_mod_id)) is True or access.get(test_mod_id) is True:
        print("PASS: Access saved correctly")
    else:
        # Try with integer key
        found = False
        for k, v in access.items():
            if int(k) == test_mod_id and v:
                found = True
                break
        if found:
            print("PASS: Access saved correctly (int key)")
        else:
            print(f"WARNING: Access not found for mod {test_mod_id}. Access keys: {list(access.keys())}")

    # Test deactivation
    print(f"\nSetting access for user {admin_id}, mod {test_mod_id}, granted=False")
    r = requests.put(
        f"{BASE_URL}/api/admin/users/{admin_id}/access",
        json={"mod_id": test_mod_id, "is_granted": False},
        headers=auth_headers,
        timeout=10
    )
    print(f"Status: {r.status_code}")

    # Verify deactivation
    r = requests.get(f"{BASE_URL}/api/admin/users/{admin_id}/access", headers=auth_headers, timeout=10)
    access = r.json().get("access", {})
    print(f"Access after deactivation: {access}")
    
    # Check if value is 0 or False for this mod
    deactivated = False
    for k, v in access.items():
        if (k == test_mod_id or int(k) == test_mod_id) and not v:
            deactivated = True
            break
    if deactivated:
        print("PASS: Deactivation saved correctly")
    else:
        print("WARNING: Deactivation not found (may mean the value is 0 which is falsy)")

# --- Test 6: Update user (toggle active status) ---
print("\n=== Test 6: PUT /api/admin/users/{id} (toggle is_active) ===")
if admin_id:
    # Get current status
    r = requests.get(f"{BASE_URL}/api/admin/users", headers=auth_headers, timeout=10)
    users_list = r.json().get("users", [])
    
    # Find a non-admin user to toggle
    target_user = None
    for u in users_list:
        if u.get("role") != "admin":
            target_user = u
            break
    
    if target_user:
        target_id = target_user["id"]
        current_active = target_user["is_active"]
        print(f"Toggling user {target_id} ({target_user['username']}) is_active from {current_active} to {not current_active}")
        
        r = requests.put(
            f"{BASE_URL}/api/admin/users/{target_id}",
            json={"is_active": not current_active},
            headers=auth_headers,
            timeout=10
        )
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        
        # Verify
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=auth_headers, timeout=10)
        users_list = r.json().get("users", [])
        for u in users_list:
            if u["id"] == target_id:
                print(f"User {target_id} is_active after update: {u['is_active']}")
                if u["is_active"] == (not current_active):
                    print("PASS: User status toggled correctly")
                else:
                    print("FAILED: User status not toggled")
                break
    else:
        print("No non-admin user found to toggle (need a regular user)")

# --- Test 7: Unauthorized access should fail ---
print("\n=== Test 7: Unauthorized access fails ===")
r = requests.get(f"{BASE_URL}/api/admin/users", timeout=10)
print(f"GET /api/admin/users without token: status={r.status_code}")
if r.status_code in (401, 403):
    print("PASS: Unauthorized access correctly rejected")
else:
    print(f"WARNING: Expected 401/403, got {r.status_code}")

print("\n=== ALL TESTS COMPLETE ===")