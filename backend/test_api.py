import requests

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    print("Testing Registration...")
    reg_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    if reg_response.status_code == 200:
        print("Registration OK")
    else:
        print("Registration Failed or User exists", reg_response.json())

    print("\nTesting Login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "test@example.com", "password": "securepassword"}
    )
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print("Login OK, got token.")
    else:
        print("Login Failed", login_response.json())
        return

    headers = {"Authorization": f"Bearer {token}"}

    print("\nTesting Token Check...")
    test_token_res = requests.post(f"{BASE_URL}/auth/test-token", headers=headers)
    print("Token Check:", test_token_res.json())

    print("\nCreating PiggyBanks (Subaccounts)...")
    pb1 = requests.post(f"{BASE_URL}/piggy-banks", headers=headers, json={"name": "Savings"}).json()
    pb2 = requests.post(f"{BASE_URL}/piggy-banks", headers=headers, json={"name": "Checking"}).json()
    print("Created PBs:", pb1, pb2)

    pb_id_1 = pb1.get("id")
    pb_id_2 = pb2.get("id")

    print("\nListing PiggyBanks...")
    pbs = requests.get(f"{BASE_URL}/piggy-banks", headers=headers).json()
    print("PiggyBanks:", pbs)

    print("\nAdding Transaction to Savings (ID 1)...")
    t1 = requests.post(
        f"{BASE_URL}/piggy-banks/{pb_id_1}/transactions",
        headers=headers,
        json={"amount": 1000.0, "description": "Initial Deposit"}
    )
    print("Initial Deposit TX:", t1.json())

    bal1 = requests.get(f"{BASE_URL}/piggy-banks/{pb_id_1}/balance", headers=headers).json()
    print("Savings Balance:", bal1)

    print("\nTesting Transfer...")
    transfer_res = requests.post(
        f"{BASE_URL}/transfers",
        headers=headers,
        json={
            "source_piggy_bank_id": pb_id_1,
            "target_piggy_bank_id": pb_id_2,
            "amount": 300.5,
            "description": "To checking"
        }
    )
    print("Transfer Result:", transfer_res.json())

    bal1_new = requests.get(f"{BASE_URL}/piggy-banks/{pb_id_1}/balance", headers=headers).json()
    bal2_new = requests.get(f"{BASE_URL}/piggy-banks/{pb_id_2}/balance", headers=headers).json()
    print("New Savings Balance:", bal1_new)
    print("New Checking Balance:", bal2_new)


if __name__ == "__main__":
    run_test()
