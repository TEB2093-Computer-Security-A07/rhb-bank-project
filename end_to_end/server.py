import os
import socket
import json
import uuid
import threading
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.models import Base, Customer, User, Transaction, TransactionType
from common.encryption import AESCipher
from common.utils import load_customers_from_csv, load_users_from_csv

logger = logging.getLogger("BankServer")
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BankServer:
    def __init__(self, host="localhost", port=9999, encrypt_packets=True):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        self.server_socket.bind((self.host, self.port))
        self.aes = AESCipher("super_secure_key")
        self.encrypt_packets = encrypt_packets

        self.engine = create_engine(f"sqlite:///tempdb_{uuid.uuid4().hex}.db")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        session = self.Session()

        try:
            logger.info("Initializing database with data from CSV files")

            customers_csv_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "common",
                "customers.csv"
            )

            customers = load_customers_from_csv(customers_csv_path)

            for customer in customers:
                customer.name = self.aes.encrypt(customer.name)
                customer.account_number = self.aes.encrypt(
                    customer.account_number)
                customer.balance = self.aes.encrypt(customer.balance)

            session.add_all(customers)
            session.commit()

            users_csv_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "common",
                "users.csv"
            )

            users = load_users_from_csv(users_csv_path, session)
            session.add_all(users)
            session.commit()

            logger.info(
                f"Added {len(customers)} customers and {len(users)} users to database")
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            session.rollback()
        finally:
            session.close()

        self.client_handlers = []

    def start(self):
        self.server_socket.listen(5)
        logger.info(f"Server started on {self.host}:{self.port}")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Connection from {addr}")
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
                self.client_handlers.append(client_thread)
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, address):
        try:
            while True:
                data = client_socket.recv(4096).decode()
                if not data:
                    break

                if self.encrypt_packets:
                    data = self.aes.decrypt(data)

                request = json.loads(data)

                response = json.dumps(self.process_request(request))

                if self.encrypt_packets:
                    response = self.aes.encrypt(response)

                client_socket.send(response.encode())

        except Exception as e:
            logger.error(f"Error handling client {address}: {str(e)}")
        finally:
            client_socket.close()
            logger.info(f"Connection closed with {address}")

    def process_request(self, request):
        action = request.get("action")

        if action == "login":
            return self.handle_login(request)
        elif action == "deposit":
            return self.handle_deposit(request)
        elif action == "withdraw":
            return self.handle_withdraw(request)
        elif action == "balance":
            return self.handle_balance(request)
        else:
            return {"status": "error", "message": "Invalid action"}

    def handle_login(self, request):
        logger.info(
            f"Received login request: {request}")
        username = request.get("username")
        password = request.get("password")

        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()

            if user and user.password == password:
                customer = user.customer
                return {
                    "status": "success",
                    "customer_id": user.customer_id,
                    "username": username,
                    "name": self.aes.decrypt(customer.name),
                    "account_number": self.aes.decrypt(customer.account_number)
                }
            else:
                return {"status": "error", "message": "Invalid credentials"}
        finally:
            session.close()

    def handle_deposit(self, request):
        customer_id = request.get("customer_id")
        amount = float(request.get("amount", 0))

        if amount <= 0:
            return {"status": "error", "message": "Invalid deposit amount"}

        session = self.Session()
        try:
            customer = session.query(Customer).filter_by(
                customer_id=customer_id).first()
            if not customer:
                return {"status": "error", "message": "Customer not found"}

            current_balance = float(self.aes.decrypt(customer.balance))
            new_balance = current_balance + amount
            customer.balance = self.aes.encrypt(str(new_balance))

            transaction = Transaction(
                customer_id=customer_id,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount
            )
            session.add(transaction)
            session.commit()

            return {
                "status": "success",
                "message": f"Deposited ${amount:.2f}",
                "new_balance": new_balance
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Deposit error: {str(e)}")
            return {"status": "error", "message": "Failed to process deposit"}
        finally:
            session.close()

    def handle_withdraw(self, request):
        customer_id = request.get("customer_id")
        amount = float(request.get("amount", 0))

        if amount <= 0:
            return {"status": "error", "message": "Invalid withdrawal amount"}

        session = self.Session()
        try:
            customer = session.query(Customer).filter_by(
                customer_id=customer_id).first()
            if not customer:
                return {"status": "error", "message": "Customer not found"}

            current_balance = float(self.aes.decrypt(customer.balance))
            if current_balance < amount:
                return {"status": "error", "message": "Insufficient funds"}

            new_balance = current_balance - amount
            customer.balance = self.aes.encrypt(str(new_balance))

            transaction = Transaction(
                customer_id=customer_id,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=amount
            )
            session.add(transaction)
            session.commit()

            return {
                "status": "success",
                "message": f"Withdrew ${amount:.2f}",
                "new_balance": new_balance
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Withdrawal error: {str(e)}")
            return {"status": "error", "message": "Failed to process withdrawal"}
        finally:
            session.close()

    def handle_balance(self, request):
        customer_id = request.get("customer_id")

        session = self.Session()
        try:
            customer = session.query(Customer).filter_by(
                customer_id=customer_id
            ).first()
            if not customer:
                return {"status": "error", "message": "Customer not found"}

            balance = float(self.aes.decrypt(customer.balance))

            return {
                "status": "success",
                "balance": balance,
                "account_number": self.aes.decrypt(customer.account_number)
            }
        finally:
            session.close()

    def cleanup(self):
        if hasattr(self, "engine") and self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")
