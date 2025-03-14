#!/usr/bin/env python3

from common.models import Customer, Base
from common.utils import load_customers_from_csv
from common.encryption import AESCipher
from data_encryption.utils import create_customer_table

import os
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


if __name__ == "__main__":
    aes = AESCipher("super_secure_key")
    console = Console()

    csv_file_path = os.path.join(
        os.path.dirname(__file__),
        "common",
        "customers.csv"
    )

    # Create engine and session
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    customers = load_customers_from_csv(csv_file_path)
    session.add_all(customers)
    session.commit()

    rows = session.query(Customer).all()

    console.print("\nUnencrypted Values:", style="bold underline")
    table_unencrypted = create_customer_table()

    for customer in rows:
        table_unencrypted.add_row(
            str(customer.customer_id),
            customer.name,
            customer.account_number,
            customer.balance
        )

    console.print(table_unencrypted)

    # Encrypt customer data and update
    for customer in rows:
        customer.name = aes.encrypt(customer.name)
        customer.account_number = aes.encrypt(customer.account_number)
        customer.balance = aes.encrypt(customer.balance)

    session.commit()

    # Query all customers again to get encrypted data
    rows = session.query(Customer).all()

    console.print("\nEncrypted Values:", style="bold underline")
    table_encrypted = create_customer_table()

    for customer in rows:
        table_encrypted.add_row(
            str(customer.customer_id),
            customer.name,
            customer.account_number,
            customer.balance
        )

    console.print(table_encrypted)

    console.print("\nDecrypted Values:", style="bold underline")
    table_decrypted = create_customer_table()

    for customer in rows:
        decrypted_name = aes.decrypt(customer.name)
        decrypted_account = aes.decrypt(customer.account_number)
        decrypted_balance = aes.decrypt(customer.balance)
        table_decrypted.add_row(
            str(customer.customer_id),
            decrypted_name,
            decrypted_account,
            decrypted_balance
        )

    console.print(table_decrypted)
    session.close()
