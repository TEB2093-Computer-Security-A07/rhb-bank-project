import time
import threading
import logging
from end_to_end.server import BankServer
from end_to_end.client import BankClient

logger = logging.getLogger("EndToEndDemo")
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

encrypt_packets = True


def run_server():
    server = BankServer(encrypt_packets=encrypt_packets)
    server.start()


def run_client():
    client = BankClient(encrypt_packets=encrypt_packets)

    if not client.connect():
        logger.error("Failed to connect to server")
        return

    try:
        if client.login():
            client.show_menu()
    finally:
        client.disconnect()


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    time.sleep(1)

    try:
        run_client()
    except KeyboardInterrupt:
        logger.info("Demo terminated by user")
