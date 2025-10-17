from notion_client import Client
from dotenv import load_dotenv
import os

# Load .env variables if running locally
load_dotenv()

# Connect to Notion
notion = Client(auth=os.getenv("NOTION_API_KEY"))
database_id = os.environ["NOTION_DATABASE_ID"]

# --- Fetch all database pages ---
data = notion.databases.query(database_id=database_id)
pages = data["results"]

income_total = 0
expense_total = 0
totals_page = None

for p in pages:
    props = p["properties"]

    # Get title
    title_prop = props.get("Title", {})
    name = ""
    if title_prop.get("title"):
        name = title_prop["title"][0]["text"]["content"]

    # Skip empty rows
    if not name:
        continue

    # Identify the "TOTALS" row
    if name.strip().lower() == "totals":
        totals_page = p
        continue

    # Collect income/expense amounts
    amount = props.get("Amount", {}).get("number")
    type_prop = props.get("Type", {}).get("select", {}).get("name")

    if amount is not None and type_prop:
        if type_prop.lower() == "income":
            income_total += amount
        elif type_prop.lower() == "expense":
            expense_total += amount

# --- Calculate net total ---
net_total = income_total - expense_total
print(f"💰 Income: {income_total}, Expenses: {expense_total}, Net: {net_total}")

# --- Prevent unnecessary updates ---
if os.path.exists("last_total.txt"):
    with open("last_total.txt", "r") as f:
        last_total = f.read().strip()
    if last_total == str(net_total):
        print("No change detected — exiting early.")
        exit(0)

with open("last_total.txt", "w") as f:
    f.write(str(net_total))

# --- Update or create the TOTALS row ---
if totals_page:
    notion.pages.update(
        page_id=totals_page["id"],
        properties={
            "Amount": {"number": net_total}
        }
    )
    print("✅ Updated 'TOTALS' row successfully!")
else:
    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Title": {"title": [{"text": {"content": "TOTALS"}}]},
            "Type": {"select": {"name": "Summary"}},
            "Category": {"select": {"name": "Net Balance"}},
            "Amount": {"number": net_total},
        }
    )
    print("🆕 Created new 'TOTALS' row successfully!")
