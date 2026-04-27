#!/usr/bin/env python3
import requests
import sqlite3
import sys
import os

# -----------------------------------------
# 全域設定與路徑配置 (Configuration & Globals)
# -----------------------------------------
# API 的基礎 URL，指向本地端運行的後端服務
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 定義 SQLite 資料庫的絕對路徑，用於直接檢查底層數據
DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "data", "bookkeeping.db")

# 全域變數，用於儲存 JWT 驗證權杖 (Token)
token = None


# -----------------------
# 介面輔助工具 (UI Helpers)
# -----------------------
def print_header(title):
    """印出美化的區段標題"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")


# --------------------------------------------
# 核心 API 通訊封裝 (API Communication Wrappers)
# --------------------------------------------
def api_get(endpoint):
    """
    封裝 GET 請求，自動帶入 Authorization Header
    
    Args:
        endpoint (str): API 的端點路徑（例如: "/piggy-banks"）
        
    Returns:
        dict: API 回傳的 JSON 格式資料
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def api_post(endpoint, json_data=None, data=None):
    """
    封裝 POST 請求：
    - 若傳入 data 參數，則使用 Form Data 格式 (用於 Login)
    - 若傳入 json_data 參數，則使用 JSON 格式 (用於一般 API)
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if data:
        r = requests.post(f"{BASE_URL}{endpoint}", data=data, headers=headers)
    else:
        r = requests.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
    return r.json()

def api_delete(endpoint):
    """
    封裝 DELETE 請求
    
    Args:
        endpoint (str): API 的端點路徑
        
    Returns:
        dict: API 回傳的 JSON 格式資料
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def api_put(endpoint, json_data):
    """ 
    封裝 PUT 請求，用於更新現有資料
    
    Args:
        endpoint (str): API 的端點路徑
        json_data (dict): 要更新的資料
        
    Returns:
        dict: API 回傳的 JSON 格式資料
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.put(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
    return r.json()


# -----------------------------
# 使用者認證功能 (Authentication)
# -----------------------------
def login():
    """
    執行登入流程並取得 JWT Token
    
    Args:
        None
        
    Returns:
        bool: 登入是否成功
    """
    global token
    print_header("身份驗證 (Authentication)")
    email = input("電子郵件 (Email): ")
    password = input("密碼 (Password): ")
    
    # 根據 OAuth2 標準，登入通常使用表單資料 (Form Data) 傳輸用戶名與密碼
    resp = api_post("/auth/login", data={"username": email, "password": password})
    if "access_token" in resp:
        token = resp["access_token"]
        print("✅ 登入成功！")
        return True
    else:
        print("❌ 登入失敗: ", resp.get("detail", "未知錯誤"))
        return False


# -----------------------------------
# 存錢筒管理功能 (PiggyBank Management)
# -----------------------------------
def list_piggybanks():
    """
    列出目前使用者所有的存錢筒及其餘額
    
    Args:
        None
        
    Returns:
        list: 存錢筒列表
    """
    print_header("您的存錢筒 (Your PiggyBanks)")
    banks = api_get("/piggy-banks")
    if not isinstance(banks, list):
        print("無法獲取資料。")
        return
    if not banks:
        print("尚未建立任何存錢筒。")
        return
    
    # 遍歷每個存錢筒並另外呼叫 API 獲取即時餘額
    for pb in banks:
        bal = api_get(f"/piggy-banks/{pb['id']}/balance")
        print(f"[{pb['id']}] {pb['name']} ({pb['currency']}) - 目前餘額: {bal.get('balance', 0)}")
    return banks

def create_piggybank():
    """
    建立新的存錢筒
    
    Args:
        None
        
    Returns:
        bool: 建立是否成功
    """
    print_header("建立存錢筒 (Create PiggyBank)")
    name = input("名稱: ")
    currency = input("貨幣單位 (預設 USD): ") or "USD"
    res = api_post("/piggy-banks", json_data={"name": name, "currency": currency})
    if "id" in res:
        print(f"✅ 存錢筒 '{name}' 建立成功！")
    else:
        print("❌ 建立失敗:", res)

def delete_piggybank():
    """
    刪除指定的存錢筒
    
    Args:
        None
        
    Returns:
        bool: 刪除是否成功
    """
    banks = list_piggybanks()
    if not banks: return
    
    try:
        pb_id = int(input("\n請輸入要刪除的存錢筒 ID: "))
        confirm = input(f"確定要刪除 ID 為 {pb_id} 的存錢筒嗎？此動作無法復原 (y/N): ")
        if confirm.lower() == 'y':
            res = api_delete(f"/piggy-banks/{pb_id}")
            if res.get("success"):
                print("✅ 刪除成功！")
            else:
                print("❌ 刪除失敗:", res)
    except ValueError:
        print("請輸入有效的數字 ID。")


# -----------------------------------
# 交易紀錄管理 (Transaction Management)
# -----------------------------------
def add_transaction():
    """
    在特定的存錢筒中新增一筆交易
    
    Args:
        None
        
    Returns:
        bool: 新增是否成功
    """
    print_header("新增交易 (Add Transaction)")
    try:
        pb_id = int(input("存錢筒 ID: "))
        amount = float(input("金額: "))
        types = ['expense (支出)', 'income (收入)', 'deposit (存款)', 'withdrawal (提款)']
        print(f"可選類型: {', '.join(types)}")
        tx_type = input("類型 (預設 expense): ") or 'expense'
        desc = input("備註/描述: ")
        
        # 簡單的邏輯：若是支出或提款，將金額轉為負數處理
        if tx_type in ['expense', 'withdrawal']:
            amount = -abs(amount)
            
        payload = {
            "amount": amount,
            "type": tx_type,
            "description": desc
        }
        
        res = api_post(f"/piggy-banks/{pb_id}/transactions", json_data=payload)
        if "id" in res:
            print("✅ 交易紀錄已成功新增！")
        else:
            print("❌ 新增失敗:", res)
    except ValueError:
        print("輸入格式錯誤（金額須為數字）。")

def edit_transaction():
    """
    修改已存在的交易紀錄
    
    Args:
        None
        
    Returns:
        bool: 修改是否成功
    """
    print_header("編輯交易 (Edit Transaction)")
    try:
        pb_id = int(input("輸入存錢筒 ID 以列出交易紀錄: "))
        txs = api_get(f"/piggy-banks/{pb_id}/transactions")
        if not txs or not isinstance(txs, list):
            print("找不到任何交易紀錄。")
            return
            
        print("\n最近的交易紀錄:")
        for tx in txs[:10]: # 只列出前 10 筆
            print(f"[{tx['id']}] {tx['date'][:10]} | {tx['type']} | {tx['amount']} | {tx['description']}")
            
        tx_id = int(input("\n請輸入欲修改的交易 ID: "))
        target_tx = next((t for t in txs if t['id'] == tx_id), None)
        if not target_tx:
            print("在該存錢筒中找不到此交易 ID。")
            return
            
        print(f"\n正在編輯交易 {tx_id}。若不修改請直接按 Enter 跳過。")
        amount_str = input(f"金額 ({target_tx['amount']}): ")
        type_str = input(f"類型 ({target_tx['type']}): ")
        desc_str = input(f"描述 ({target_tx['description']}): ")
        cat_str = input(f"分類 ({target_tx['category'] or '無'}): ")
        
        # 僅將有更動的部分放入 payload
        payload = {}
        if amount_str: payload['amount'] = float(amount_str)
        if type_str: payload['type'] = type_str
        if desc_str: payload['description'] = desc_str
        if cat_str: payload['category'] = cat_str
        
        if not payload:
            print("未偵測到任何更動。")
            return
            
        res = api_put(f"/transactions/{tx_id}", json_data=payload)
        if "id" in res:
            print("✅ 交易紀錄已更新！")
        else:
            print("❌ 更新失敗:", res)
            
    except ValueError:
        print("輸入格式錯誤。")


# ----------------------------------
# 資料庫直接診斷 (Database Inspection)
# ----------------------------------
def inspect_db():
    """
    直接讀取 SQLite 檔案，繞過 API 檢查原始數據（偵錯用）
    
    Args:
        None
        
    Returns:
        None
    """
    print_header("原始資料庫檢查 (Raw Database Inspection)")
    if not os.path.exists(DB_PATH):
        print(f"❌ 在路徑找不到資料庫檔案: {DB_PATH}")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查詢所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("資料庫中的資料表:", [t[0] for t in tables])
        
        # 抽樣印出前 3 筆資料
        for table in ['users', 'piggy_banks', 'transactions']:
            print(f"\n--- {table} 表的前 3 筆資料 ---")
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                if not rows:
                    print(" (目前為空)")
                for r in rows:
                    print(r)
            except sqlite3.OperationalError:
                print(" 該資料表不存在。")
                
        conn.close()
    except Exception as e:
        print("資料庫連線錯誤:", e)


# -----------------------------------------
# 主迴圈與使用者介面控制 (Main Loop & UI Logic)
# -----------------------------------------
def main_loop():
    """
    CLI 主程式入口
    
    Args:
        None
        
    Returns:
        None
    """
    print("歡迎使用 PiggyNest 互動式命令行工具！")
    while True:
        # 尚未登入時的選單
        if not token:
            print("\n選項: (1) 登入 (q) 結束程式")
            choice = input("> ")
            if choice == '1':
                login()
            elif choice == 'q':
                break
        # 登入後的選單
        else:
            print("\n--- 主選單 ---")
            print("1) 列出存錢筒與餘額")
            print("2) 建立新存錢筒")
            print("3) 刪除存錢筒")
            print("4) 新增交易紀錄")
            print("5) 編輯交易紀錄")
            print("6) 檢查原始資料庫 (Debug)")
            print("q) 登出並退出")
            choice = input("> ")
            
            if choice == '1':
                list_piggybanks()

            elif choice == '2':
                create_piggybank()

            elif choice == '3':
                delete_piggybank()

            elif choice == '4':
                add_transaction()

            elif choice == '5':
                edit_transaction()

            elif choice == '6':
                inspect_db()

            elif choice == 'q':
                print("再見！")
                break
                
            else:
                print("無效的選項，請重新輸入。")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        # 處理 Ctrl+C 強制結束的情境
        print("\n偵測到中斷訊息，正在關閉程式...")
        sys.exit(0)