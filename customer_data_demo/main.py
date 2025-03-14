#!/usr/bin/env python3

import sqlite3
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from rich.console import Console
from rich.table import Table


class Customer:
    def __init__(
        self,
        name: str,
        account_number: str,
        balance: str,
        customer_id: int | None = None
    ):
        self.name = name
        self.account_number = account_number
        self.balance = balance
        self.customer_id = customer_id

    def to_tuple(self, with_id: bool = False):
        result = (self.name, self.account_number, self.balance)
        if with_id and self.customer_id:
            result = result + (self.customer_id,)
        return result


class AESCipher:
    def __init__(self, key: str):
        self.block_size = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, decrypted_content: str) -> str:
        """Encrypts a string and returns Base64-encoded ciphertext."""
        content_padded = self._pad(decrypted_content)

        initialization_vector = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, initialization_vector)
        return base64.b64encode(
            initialization_vector + cipher.encrypt(content_padded.encode())
        ).decode()

    def decrypt(self, encrypted_content: str) -> str:
        """Decrypts a Base64-encoded ciphertext and returns the original string."""
        encrypted_content = base64.b64decode(encrypted_content)
        iv = encrypted_content[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        decrypted_padded = cipher.decrypt(encrypted_content[AES.block_size:])
        return self._unpad(decrypted_padded).decode('utf-8')

    def _pad(self, content: str) -> str:
        """Applies PKCS7 padding to match AES block size."""
        return content + (self.block_size - len(content) % self.block_size) * chr(self.block_size - len(content) % self.block_size)

    @staticmethod
    def _unpad(content: str) -> str:
        """Removes PKCS7 padding."""
        return content[:-ord(content[len(content)-1:])]


class DbOperations:
    @staticmethod
    def insert_data(customer: Customer, cursor: sqlite3.Cursor, connection: sqlite3.Connection):
        cursor.execute(
            "INSERT INTO customers (name, account_number, balance) VALUES (?, ?, ?)",
            customer.to_tuple()
        )
        connection.commit()
        customer.customer_id = cursor.lastrowid

    @staticmethod
    def update_data(customer: Customer, cursor: sqlite3.Cursor, connection: sqlite3.Connection):
        cursor.execute(
            "UPDATE customers SET name = ?, account_number = ?, balance = ? WHERE id = ?",
            customer.to_tuple(with_id=True)
        )
        connection.commit()


if __name__ == "__main__":
    aes = AESCipher("my_secure_password")
    console = Console()

    customers = [
        Customer(
            name="Ammar Farhan Mohamad Rizam",
            account_number="1234-5678-9012",
            balance="1000.50"
        ),
        Customer(
            name="Ahmad Anas Azhar",
            account_number="2345-6789-0123",
            balance="2500.75"
        ),
        Customer(
            name="Amisya Fareezan Mohd Fadhil",
            account_number="3456-7890-1234",
            balance="300.00"
        ),
        Customer(
            name="Muhammad Hanis Afifi Azmi",
            account_number="4567-8901-2345",
            balance="1500.00"
        ),
    ]

    with sqlite3.connect(":memory:") as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                account_number TEXT,
                balance TEXT
            )
        """)

        for customer in customers:
            DbOperations.insert_data(
                customer=customer,
                cursor=cursor,
                connection=connection
            )

        cursor.execute(
            "SELECT id, name, account_number, balance FROM customers")
        rows = cursor.fetchall()

        console.print("\nUnencrypted Values:", style="bold underline")
        table_unencrypted = Table(
            show_header=True, header_style="bold magenta")
        table_unencrypted.add_column("ID")
        table_unencrypted.add_column("Name")
        table_unencrypted.add_column("Account Number")
        table_unencrypted.add_column("Balance")

        for customer in rows:
            table_unencrypted.add_row(
                str(customer[0]),
                customer[1],
                customer[2],
                customer[3]
            )

        console.print(table_unencrypted)

        for row in rows:
            encrypted_name = aes.encrypt(row[1])
            encrypted_account = aes.encrypt(row[2])
            encrypted_balance = aes.encrypt(row[3])
            encrypted_customer = Customer(
                name=encrypted_name,
                account_number=encrypted_account,
                balance=encrypted_balance,
                customer_id=row[0]
            )
            DbOperations.update_data(
                customer=encrypted_customer,
                cursor=cursor,
                connection=connection
            )

        cursor.execute(
            "SELECT id, name, account_number, balance FROM customers")
        rows = cursor.fetchall()

        console.print("\nEncrypted Values:", style="bold underline")
        table_encrypted = Table(show_header=True, header_style="bold magenta")
        table_encrypted.add_column("ID")
        table_encrypted.add_column("Name")
        table_encrypted.add_column("Account Number")
        table_encrypted.add_column("Balance")

        for customer in rows:
            table_encrypted.add_row(
                str(customer[0]),
                customer[1],
                customer[2],
                customer[3]
            )

        console.print(table_encrypted)

        console.print("\nDecrypted Values:", style="bold underline")
        table_decrypted = Table(show_header=True, header_style="bold magenta")
        table_decrypted.add_column("ID")
        table_decrypted.add_column("Name")
        table_decrypted.add_column("Account Number")
        table_decrypted.add_column("Balance")

        for customer in rows:
            decrypted_name = aes.decrypt(customer[1])
            decrypted_account = aes.decrypt(customer[2])
            decrypted_balance = aes.decrypt(customer[3])
            table_decrypted.add_row(
                str(customer[0]),
                decrypted_name,
                decrypted_account,
                decrypted_balance
            )

        console.print(table_decrypted)
