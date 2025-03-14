#!/usr/bin/env python3

from rich.table import Table


def create_customer_table() -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Customer ID")
    table.add_column("Name")
    table.add_column("Account Number")
    table.add_column("Balance")
    return table
