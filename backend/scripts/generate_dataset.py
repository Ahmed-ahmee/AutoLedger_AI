"""
Generate realistic synthetic financial transactions based on a Chart of Accounts.
Produces:
  - data/chart_of_accounts.csv  (19 GL codes)
  - data/synthetic_transactions.csv  (1,000 transactions)
"""

import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# ── Chart of Accounts ──────────────────────────────────────────────────
COA = [
    # Assets (1000–1999)
    ("1100", "Cash & Bank",           "Assets",      "Cash & Bank"),
    ("1200", "Accounts Receivable",   "Assets",      "Accounts Receivable"),
    ("1300", "Inventory",             "Assets",      "Inventory"),
    # Liabilities (2000–2999)
    ("2100", "Accounts Payable",      "Liabilities", "Accounts Payable"),
    ("2200", "Accrued Expenses",      "Liabilities", "Accrued Expenses"),
    # Equity (3000–3999)
    ("3100", "Retained Earnings",     "Equity",      "Retained Earnings"),
    # Revenue (4000–4999)
    ("4100", "Product Sales",         "Revenue",     "Product Sales"),
    ("4200", "Service Revenue",       "Revenue",     "Service Revenue"),
    # Expenses (5000–6999)
    ("5100", "Office Supplies",       "Expenses",    "Office Supplies"),
    ("5200", "Travel Expense",        "Expenses",    "Travel"),
    ("5300", "Utilities",             "Expenses",    "Utilities"),
    ("5400", "Software Subscriptions","Expenses",    "Software"),
    ("5500", "Professional Fees",     "Expenses",    "Professional Services"),
    ("5600", "Commission Expense",    "Expenses",    "Commissions"),
    ("5700", "Rent Expense",          "Expenses",    "Rent"),
    ("5800", "Marketing Expense",     "Expenses",    "Marketing"),
    ("5900", "Salaries Expense",      "Expenses",    "Salaries"),
    ("6100", "Insurance Expense",     "Expenses",    "Insurance"),
    ("6200", "Depreciation Expense",  "Expenses",    "Depreciation"),
]

# ── Transaction templates per GL code ─────────────────────────────────
TEMPLATES = {
    "1100": {
        "descriptions": [
            "Bank transfer received from {vendor}",
            "Wire transfer deposit – {vendor}",
            "ACH deposit from {vendor}",
            "Petty cash replenishment",
            "Cash deposit at branch office",
            "Bank interest earned",
            "ATM withdrawal for operations",
        ],
        "vendors": ["Chase Bank", "Wells Fargo", "Bank of America", "Citibank", "PNC Financial"],
        "amount_range": (500, 50000),
    },
    "1200": {
        "descriptions": [
            "Invoice #{ref} – {vendor} payment pending",
            "Client payment due from {vendor}",
            "Outstanding receivable – project #{ref}",
            "Customer balance – {vendor} Q{q} billing",
            "Trade receivable from {vendor}",
        ],
        "vendors": ["Acme Corp", "GlobalTech", "Pinnacle Industries", "Vertex Solutions", "Meridian Holdings"],
        "amount_range": (1000, 75000),
    },
    "1300": {
        "descriptions": [
            "Inventory purchase – raw materials from {vendor}",
            "Stock replenishment order #{ref}",
            "Warehouse receipt – {vendor} delivery",
            "Bulk materials procurement from {vendor}",
            "Inventory adjustment – cycle count",
        ],
        "vendors": ["SupplyChain Pro", "MaterialWorld", "Grainger", "Fastenal", "McMaster-Carr"],
        "amount_range": (2000, 60000),
    },
    "2100": {
        "descriptions": [
            "Vendor invoice from {vendor} – due net 30",
            "AP entry – {vendor} supplies",
            "Outstanding payable to {vendor}",
            "Supplier bill #{ref} – {vendor}",
            "Trade payable – {vendor} procurement",
        ],
        "vendors": ["Dell Technologies", "HP Inc", "Sysco Corp", "Staples", "Office Depot"],
        "amount_range": (500, 40000),
    },
    "2200": {
        "descriptions": [
            "Accrued wages payable – {dept} department",
            "Accrued interest on credit facility",
            "Accrued tax liability – Q{q}",
            "Accrued bonus provision – {dept}",
            "Accrued utility charges – {vendor}",
        ],
        "vendors": ["Internal", "ADP Payroll", "Tax Authority", "Benefits Provider"],
        "amount_range": (1000, 30000),
    },
    "3100": {
        "descriptions": [
            "Retained earnings adjustment – FY closing",
            "Dividend declaration – Q{q} distribution",
            "Net income transfer to retained earnings",
            "Prior period adjustment – retained earnings",
        ],
        "vendors": ["Internal"],
        "amount_range": (10000, 200000),
    },
    "4100": {
        "descriptions": [
            "Product sale to {vendor} – order #{ref}",
            "Revenue from {vendor} – bulk purchase",
            "Online sales revenue – batch #{ref}",
            "Wholesale product shipment to {vendor}",
            "Point of sale transaction – store #{ref}",
            "Product licensing revenue from {vendor}",
        ],
        "vendors": ["Amazon", "Walmart", "Target", "Costco", "Best Buy", "Home Depot"],
        "amount_range": (100, 150000),
    },
    "4200": {
        "descriptions": [
            "Consulting engagement – {vendor} project",
            "Professional services rendered to {vendor}",
            "Monthly retainer – {vendor} advisory",
            "Service contract revenue – {vendor}",
            "Implementation services – project #{ref}",
        ],
        "vendors": ["Deloitte", "PwC Engagement", "McKinsey", "Bain & Co", "Boston Consulting"],
        "amount_range": (5000, 100000),
    },
    "5100": {
        "descriptions": [
            "Office supplies purchase from {vendor}",
            "Printer toner and paper – {vendor}",
            "Stationery order #{ref} from {vendor}",
            "Desk accessories and organizers – {vendor}",
            "Breakroom supplies from {vendor}",
        ],
        "vendors": ["Staples", "Office Depot", "Amazon Business", "W.B. Mason", "Quill"],
        "amount_range": (25, 2500),
    },
    "5200": {
        "descriptions": [
            "Flight booking – {dept} team to conference",
            "Hotel accommodation – {vendor} business trip",
            "Uber/Lyft rides – {dept} travel",
            "Per diem expenses – client visit {vendor}",
            "Car rental – {vendor} for site inspection",
            "Travel reimbursement – employee #{ref}",
        ],
        "vendors": ["Delta Airlines", "Marriott Hotels", "Hilton", "United Airlines", "Hertz Rental"],
        "amount_range": (100, 8000),
    },
    "5300": {
        "descriptions": [
            "Monthly electricity bill – {vendor}",
            "Water and sewage charges – {vendor}",
            "Natural gas utility – {vendor}",
            "Internet service – {vendor} fiber plan",
            "Telephone/VoIP charges – {vendor}",
        ],
        "vendors": ["ConEdison", "Pacific Gas & Electric", "Comcast Business", "AT&T", "Verizon"],
        "amount_range": (200, 5000),
    },
    "5400": {
        "descriptions": [
            "Annual license – {vendor} enterprise plan",
            "Monthly SaaS subscription – {vendor}",
            "Cloud hosting charges – {vendor}",
            "Software renewal – {vendor} platform",
            "Developer tools subscription – {vendor}",
        ],
        "vendors": ["Microsoft 365", "Salesforce", "AWS", "Google Workspace", "Slack", "Jira Atlassian", "Adobe Creative Cloud"],
        "amount_range": (50, 15000),
    },
    "5500": {
        "descriptions": [
            "Legal consultation fee – {vendor}",
            "Accounting & audit services – {vendor}",
            "Tax preparation – {vendor} engagement",
            "HR consulting retainer – {vendor}",
            "External audit fee – {vendor} FY review",
        ],
        "vendors": ["Baker McKenzie", "KPMG", "Ernst & Young", "Grant Thornton", "BDO"],
        "amount_range": (1000, 50000),
    },
    "5600": {
        "descriptions": [
            "Sales commission – {dept} team Q{q}",
            "Referral bonus payout – partner {vendor}",
            "Agent commission – contract #{ref}",
            "Performance bonus – sales rep #{ref}",
            "Channel partner commission – {vendor}",
        ],
        "vendors": ["Internal Sales", "Partner Network", "Channel Partners", "Sales Team"],
        "amount_range": (500, 25000),
    },
    "5700": {
        "descriptions": [
            "Monthly office rent – {vendor} building",
            "Warehouse lease payment – {vendor}",
            "Co-working space rental – {vendor}",
            "Parking facility lease – {vendor}",
            "Storage unit rental – {vendor}",
        ],
        "vendors": ["CBRE Group", "JLL", "WeWork", "Regus", "Brookfield Properties"],
        "amount_range": (2000, 30000),
    },
    "5800": {
        "descriptions": [
            "Google Ads campaign – {dept} budget Q{q}",
            "Social media advertising – {vendor}",
            "Trade show booth – {vendor} expo",
            "Print media advertisement – {vendor}",
            "Content marketing services – {vendor}",
            "Email campaign platform – {vendor}",
            "Influencer partnership – {vendor}",
        ],
        "vendors": ["Google Ads", "Meta Ads", "LinkedIn Marketing", "HubSpot", "Mailchimp", "Trade Show Inc"],
        "amount_range": (200, 20000),
    },
    "5900": {
        "descriptions": [
            "Monthly payroll – {dept} department",
            "Bi-weekly salary disbursement – {dept}",
            "Employee wages – pay period #{ref}",
            "Overtime compensation – {dept} team",
            "Contractor payment – {vendor}",
        ],
        "vendors": ["ADP Payroll", "Paychex", "Gusto", "Internal HR"],
        "amount_range": (3000, 120000),
    },
    "6100": {
        "descriptions": [
            "General liability insurance premium – {vendor}",
            "Workers compensation insurance – {vendor}",
            "Property insurance renewal – {vendor}",
            "D&O insurance policy – {vendor}",
            "Cyber liability insurance – {vendor}",
        ],
        "vendors": ["State Farm", "Allianz", "AIG", "Chubb", "Hartford"],
        "amount_range": (500, 15000),
    },
    "6200": {
        "descriptions": [
            "Monthly depreciation – office equipment",
            "Depreciation – computer hardware Q{q}",
            "Vehicle depreciation – fleet #{ref}",
            "Furniture & fixtures depreciation",
            "Leasehold improvements amortization",
        ],
        "vendors": ["Internal"],
        "amount_range": (500, 10000),
    },
}

DEPARTMENTS = [
    "Finance", "Engineering", "Sales", "Marketing",
    "Operations", "HR", "Legal", "IT", "Executive"
]


def generate_description(template: str, vendor: str, dept: str) -> str:
    """Fill in placeholders in the description template."""
    ref = random.randint(1000, 9999)
    q = random.randint(1, 4)
    return template.format(vendor=vendor, dept=dept, ref=ref, q=q)


def generate_dataset(output_dir: str, n_transactions: int = 1000):
    """Generate COA + synthetic transactions CSVs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # ── Write Chart of Accounts ────────────────────────────────────────
    coa_file = output_path / "chart_of_accounts.csv"
    with open(coa_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["gl_code", "gl_name", "category", "sub_category"])
        for row in COA:
            writer.writerow(row)
    print(f"✓ Chart of Accounts saved: {coa_file}  ({len(COA)} accounts)")

    # ── Generate Transactions ──────────────────────────────────────────
    txn_file = output_path / "synthetic_transactions.csv"
    gl_codes = [c[0] for c in COA]

    # Weight GL codes so expense categories appear more frequently (realistic)
    weights = []
    for code in gl_codes:
        if code.startswith("5") or code.startswith("6"):
            weights.append(3)  # expenses are more frequent
        elif code.startswith("4"):
            weights.append(2)  # revenue next
        else:
            weights.append(1)

    base_date = datetime(2024, 1, 1)
    transactions = []

    for i in range(n_transactions):
        gl_code = random.choices(gl_codes, weights=weights, k=1)[0]
        tmpl = TEMPLATES[gl_code]

        vendor = random.choice(tmpl["vendors"])
        dept = random.choice(DEPARTMENTS)
        desc_template = random.choice(tmpl["descriptions"])
        description = generate_description(desc_template, vendor, dept)

        lo, hi = tmpl["amount_range"]
        amount = round(random.uniform(lo, hi), 2)

        txn_date = base_date + timedelta(days=random.randint(0, 364))

        transactions.append({
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "description": description,
            "amount": amount,
            "vendor": vendor,
            "department": dept,
            "gl_code": gl_code,  # ground truth for evaluation
        })

    # Shuffle for realism
    random.shuffle(transactions)

    with open(txn_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["transaction_date", "description", "amount", "vendor", "department", "gl_code"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    print(f"✓ Synthetic transactions saved: {txn_file}  ({n_transactions} rows)")
    return str(coa_file), str(txn_file)


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    generate_dataset(data_dir, n_transactions=1000)
