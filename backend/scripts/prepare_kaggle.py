import pandas as pd
import os

def prepare_kaggle_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data')
    excel_path = os.path.join(data_dir, 'gl_transactions.xlsx')
    
    print("Loading Excel file...")
    # Load Chart of Accounts
    coa_df = pd.read_excel(excel_path, sheet_name='Chart of Accounts')
    
    # Map to our standard COA format
    # Columns in Excel: Account_key, Class, SubClass, Account
    new_coa = pd.DataFrame({
        'gl_code': coa_df['Account_key'].astype(str),
        'gl_name': coa_df['Account'],
        'category': coa_df['Class'],
        'sub_category': coa_df['SubClass']
    })
    
    # Handle missing values
    new_coa['category'] = new_coa['category'].fillna('Uncategorized')
    new_coa['sub_category'] = new_coa['sub_category'].fillna('')
    
    # Save COA
    coa_out = os.path.join(data_dir, 'chart_of_accounts.csv')
    new_coa.to_csv(coa_out, index=False)
    print(f"Saved {len(new_coa)} accounts to {coa_out}")
    
    # Load Transactions
    txn_df = pd.read_excel(excel_path, sheet_name='GL')
    
    # We want to create synthetic_transactions.csv (or a new kaggle one)
    # Excel cols: EntryNo, Date, Territory_key, Account_key, Details, Amount ...
    new_txn = pd.DataFrame({
        'transaction_date': pd.to_datetime(txn_df['Date']).dt.strftime('%Y-%m-%d'),
        'description': txn_df['Details'],
        'amount': txn_df['Amount'].abs(),  # keep absolute for normal expenses (or just original)
        'vendor': 'Kaggle Vendor',
        'department': 'Finance',
        'true_gl_code': txn_df['Account_key'].astype(str) # For reference
    })
    
    # Fill NAs
    new_txn['description'] = new_txn['description'].fillna('Misc Transaction')
    
    txn_out = os.path.join(data_dir, 'kaggle_transactions.csv')
    new_txn.to_csv(txn_out, index=False)
    print(f"Saved {len(new_txn)} transactions to {txn_out}")

if __name__ == "__main__":
    prepare_kaggle_data()
