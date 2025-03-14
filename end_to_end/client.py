import socket
import json
import logging
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.panel import Panel
from common.encryption import AESCipher

logger = logging.getLogger("BankClient")
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BankClient:
    def __init__(self, host="localhost", port=9999, encrypt_packets=True):
        self.host = host
        self.port = port
        self.aes = AESCipher("super_secure_key")
        self.console = Console()
        self.customer_id = None
        self.username = None
        self.name = None
        self.account_number = None
        self.encrypt_packets = encrypt_packets

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            return True
        except ConnectionRefusedError:
            logger.error(
                "Could not connect to the server. Is the server running?")
            return False

    def disconnect(self):
        if hasattr(self, "client_socket"):
            self.client_socket.close()

    def send_request(self, request):
        data = json.dumps(request)
        if self.encrypt_packets:
            data = self.aes.encrypt(data)

        self.client_socket.send(data.encode())

        data = self.client_socket.recv(4096).decode()

        if self.encrypt_packets:
            data = self.aes.decrypt(data)

        return json.loads(data)

    def login(self):
        self.console.print(
            Panel.fit("[bold blue]Welcome to the Secure Banking System[/bold blue]"))

        username = Prompt.ask("[green]Username")
        password = Prompt.ask("[green]Password", password=True)

        response = self.send_request({
            "action": "login",
            "username": username,
            "password": password
        })

        if response.get("status") == "success":
            self.customer_id = response.get("customer_id")
            self.username = response.get("username")
            self.name = response.get("name")
            self.account_number = response.get("account_number")

            self.console.print(
                f"[bold green]Welcome, {self.name}![/bold green]")
            return True
        else:
            message = response.get("message")
            self.console.print(
                f"[bold red]Login failed: {message}[/bold red]")
            return False

    def show_balance(self):
        response = self.send_request({
            "action": "balance",
            "customer_id": self.customer_id
        })

        if response.get("status") == "success":
            balance = response.get("balance")
            account_number = response.get("account_number")
            self.console.print(
                f"[bold green]Current Balance: ${balance:.2f}[/bold green]")
            self.console.print(
                f"Account Number: {account_number}")
        else:
            message = response.get("message")
            self.console.print(
                f"[bold red]Error: {message}[/bold red]")

    def deposit(self):
        amount = FloatPrompt.ask("[green]Enter deposit amount")

        response = self.send_request({
            "action": "deposit",
            "customer_id": self.customer_id,
            "amount": amount
        })

        if response.get("status") == "success":
            message = response.get("message")
            new_balance = response.get("new_balance")
            self.console.print(
                f"[bold green]{message}[/bold green]")
            self.console.print(
                f"[green]New Balance: ${new_balance:.2f}[/green]")
        else:
            message = response.get("message")
            self.console.print(
                f"[bold red]Error: {message}[/bold red]")

    def withdraw(self):
        amount = FloatPrompt.ask("[green]Enter withdrawal amount")

        response = self.send_request({
            "action": "withdraw",
            "customer_id": self.customer_id,
            "amount": amount
        })

        if response.get("status") == "success":
            message = response.get("message")
            new_balance = response.get("new_balance")
            self.console.print(
                f"[bold green]{message}[/bold green]")
            self.console.print(
                f"[green]New Balance: ${new_balance:.2f}[/green]")
        else:
            message = response.get("message")
            self.console.print(
                f"[bold red]Error: {message}[/bold red]")

    def show_menu(self):
        while True:
            self.console.print(
                Panel.fit("[bold blue]Banking Options[/bold blue]"))
            self.console.print("[1] Show Balance")
            self.console.print("[2] Deposit")
            self.console.print("[3] Withdraw")
            self.console.print("[4] Logout")

            choice = IntPrompt.ask(
                "[green]Enter your choice",
                choices=["1", "2", "3", "4"]
            )

            if choice == 1:
                self.show_balance()
            elif choice == 2:
                self.deposit()
            elif choice == 3:
                self.withdraw()
            elif choice == 4:
                self.console.print("[yellow]Logging out...[/yellow]")
                break

            self.console.input("\nPress Enter to continue...")
