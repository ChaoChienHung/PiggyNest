import pandas as pd
from datetime import datetime

# 初始化交易紀錄的 DataFrame
columns = ['Transaction ID', 'Date', 'Amount', 'Category', 'Description']
transactions_df = pd.DataFrame(columns=columns)

# 初始化交易ID計數器
transaction_counter = 1

# 記錄交易
def record_transaction(date, amount, category, description):
    global transaction_counter, transactions_df
    transaction_id = transaction_counter
    transaction_counter += 1
    transaction = {
        'Transaction ID': transaction_id,
        'Date': pd.to_datetime(date),
        'Amount': amount,
        'Category': category,
        'Description': description
    }
    transactions_df.loc[len(transactions_df)] = transaction
    print(f"✅ 交易已記錄: {transaction}\n")

# 生成月度報告
def generate_monthly_report(year, month):
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    monthly_transactions = transactions_df[(transactions_df['Date'] >= start_date) & (transactions_df['Date'] < end_date)]
    total_income = monthly_transactions[monthly_transactions['Amount'] > 0]['Amount'].sum()
    total_expenses = monthly_transactions[monthly_transactions['Amount'] < 0]['Amount'].sum()
    balance = total_income + total_expenses

    print(f"\n--- {year}-{month:02d} 月度報告 ---")
    print(f"總收入: {total_income:.2f} 元")
    print(f"總支出: {total_expenses:.2f} 元")
    print(f"結餘: {balance:.2f} 元\n")

    if not monthly_transactions.empty:
        print("📊 各分類支出/收入：")
        category_summary = monthly_transactions.groupby('Category')['Amount'].sum().sort_values()
        for category, amount in category_summary.items():
            print(f"- {category}: {amount:.2f} 元")

# 生成年度報告
def generate_yearly_report(year):
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)

    yearly_transactions = transactions_df[(transactions_df['Date'] >= start_date) & (transactions_df['Date'] < end_date)]
    total_income = yearly_transactions[yearly_transactions['Amount'] > 0]['Amount'].sum()
    total_expenses = yearly_transactions[yearly_transactions['Amount'] < 0]['Amount'].sum()
    balance = total_income + total_expenses

    print(f"\n=== {year} 年度報告 ===")
    print(f"總收入: {total_income:.2f} 元")
    print(f"總支出: {total_expenses:.2f} 元")
    print(f"結餘: {balance:.2f} 元\n")

    if not yearly_transactions.empty:
        print("📊 各分類支出/收入：")
        category_summary = yearly_transactions.groupby('Category')['Amount'].sum().sort_values()
        for category, amount in category_summary.items():
            print(f"- {category}: {amount:.2f} 元")

def save_to_csv(filename='transactions.csv'):
    transactions_df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"📄 資料已儲存為 CSV 檔案: {filename}")

def save_to_excel(filename='transactions.xlsx'):
    transactions_df.to_excel(filename, index=False)
    print(f"📊 資料已儲存為 Excel 檔案: {filename}")

def load_from_csv(filename='transactions.csv'):
    global transactions_df, transaction_counter
    try:
        transactions_df = pd.read_csv(filename, parse_dates=['Date'])
        transaction_counter = transactions_df['Transaction ID'].max() + 1
        print(f"✅ 成功從 CSV 載入 {len(transactions_df)} 筆資料")
    except FileNotFoundError:
        print(f"⚠️ 找不到 {filename}，將從空白開始。")

def load_from_excel(filename='transactions.xlsx'):
    global transactions_df, transaction_counter
    try:
        transactions_df = pd.read_excel(filename, parse_dates=['Date'])
        transaction_counter = transactions_df['Transaction ID'].max() + 1
        print(f"✅ 成功從 Excel 載入 {len(transactions_df)} 筆資料")
    except FileNotFoundError:
        print(f"⚠️ 找不到 {filename}，將從空白開始。")

def menu():
    while True:
        print("\n📘 選單：")
        print("1. 新增交易")
        print("2. 查看月度報告")
        print("3. 查看年度報告")
        print("4. 儲存資料 (CSV / Excel)")
        print("5. 載入資料 (CSV / Excel)")
        print("6. 離開")
        choice = input("請輸入選項 (1-6): ")

        if choice == '1':
            date = input("輸入日期 (YYYY-MM-DD): ")
            amount = float(input("輸入金額 (收入為正，支出為負): "))
            category = input("輸入分類 (如：Food, Salary, Transport): ")
            description = input("輸入描述: ")
            record_transaction(date, amount, category, description)

        elif choice == '2':
            year = int(input("輸入年份 (YYYY): "))
            month = int(input("輸入月份 (1-12): "))
            generate_monthly_report(year, month)

        elif choice == '3':
            year = int(input("輸入年份 (YYYY): "))
            generate_yearly_report(year)

        elif choice == '4':
            save_to_csv()
            save_to_excel()

        elif choice == '5':
            file_type = input("輸入檔案類型 (csv / excel): ").strip().lower()
            if file_type == 'csv':
                load_from_csv()
            elif file_type == 'excel':
                load_from_excel()
            else:
                print("❌ 不支援的檔案格式。")

        elif choice == '6':
            print("👋 程式結束，再見！")
            break

        else:
            print("❌ 無效的選項，請重新輸入。")

load_from_csv()
# 啟動主選單
menu()