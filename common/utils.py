import csv
from .models import Customer, User


def load_customers_from_csv(csv_file_path: str):
    customers = []
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            customer = Customer(
                name=row["name"],
                account_number=row["account_number"],
                balance=row["balance"]
            )
            customers.append(customer)
    return customers


def generate_customer_csv(file_path: str, customers: list):
    with open(file_path, mode="w", encoding="utf-8", newline="") as file:
        fieldnames = ["name", "account_number", "balance"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for customer in customers:
            writer.writerow(
                {
                    "name": customer.name,
                    "account_number": customer.account_number,
                    "balance": customer.balance
                }
            )


def load_users_from_csv(csv_file_path: str, session):
    """
    Load user data from CSV and associate with existing customers
    """
    users = []
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            user = User(
                username=row["username"],
                password=row["password"],
                customer_id=row["customer_id"]
            )
            users.append(user)

    return users
