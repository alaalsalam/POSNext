"""Non-destructive two-transaction InnoDB lock acceptance for Milestone 2.

The real ERPNext accounting acceptance remains rollback-only, so its uncommitted QA
documents cannot be observed by independent connections. This runner exercises the
same outstanding-row serialization invariant with two real database connections and
drops its uniquely named QA table in all cases.
"""

import os
import sys
import threading
import time
import traceback

import frappe
import MySQLdb

BENCH_PATH = "/home/erpnext/frappe-bench16"
SITE = "digitpos.trilogy-erp.com"


def _connection(options):
	return MySQLdb.connect(**options)


def _connection_options():
	options = {
		"user": frappe.conf.get("db_user") or frappe.conf.db_name,
		"passwd": frappe.conf.db_password,
		"db": frappe.conf.db_name,
		"charset": "utf8mb4",
	}
	if frappe.conf.get("db_socket"):
		options["unix_socket"] = frappe.conf.db_socket
	else:
		options["host"] = frappe.conf.get("db_host") or "127.0.0.1"
		options["port"] = int(frappe.conf.get("db_port") or 3306)
	return options


def run():
	os.chdir(BENCH_PATH)
	frappe.init(site=SITE, sites_path=f"{BENCH_PATH}/sites")
	frappe.connect()
	table = f"tabPOSNext QA Concurrency {os.getpid()}"
	quoted_table = f"`{table}`"
	connections = []
	results = []
	results_lock = threading.Lock()
	barrier = threading.Barrier(2)
	try:
		frappe.db.sql(
			f"""CREATE TABLE {quoted_table} (
				record_id varchar(80) PRIMARY KEY,
				outstanding decimal(21,9) NOT NULL DEFAULT 0,
				allocated decimal(21,9) NOT NULL DEFAULT 0
			) ENGINE=InnoDB"""
		)
		frappe.db.sql(
			f"INSERT INTO {quoted_table} (record_id, outstanding) VALUES ('invoice', 100)"
		)
		frappe.db.commit()
		connection_options = _connection_options()

		def attempt(payment_id):
			connection = None
			cursor = None
			try:
				connection = _connection(connection_options)
				with results_lock:
					connections.append(connection)
				cursor = connection.cursor()
				connection.autocommit(False)
				cursor.execute("SELECT CONNECTION_ID()")
				connection_id = cursor.fetchone()[0]
				barrier.wait(timeout=5)
				started = time.monotonic()
				cursor.execute(
					f"SELECT outstanding FROM {quoted_table} WHERE record_id = 'invoice' FOR UPDATE"
				)
				outstanding = float(cursor.fetchone()[0])
				lock_wait = time.monotonic() - started
				if outstanding >= 100:
					cursor.execute(
						f"UPDATE {quoted_table} SET outstanding = outstanding - 100 WHERE record_id = 'invoice'"
					)
					cursor.execute(
						f"INSERT INTO {quoted_table} (record_id, allocated) VALUES (%s, 100)",
						(payment_id,),
					)
					time.sleep(0.75)
					connection.commit()
					status = "submitted"
				else:
					connection.rollback()
					status = "rejected"
				with results_lock:
					results.append({
						"payment": payment_id,
						"connection_id": connection_id,
						"status": status,
						"observed_outstanding": outstanding,
						"lock_wait_seconds": round(lock_wait, 3),
					})
			except Exception as error:
				if connection:
					connection.rollback()
				with results_lock:
					results.append({"payment": payment_id, "status": "error", "error": str(error)})
			finally:
				if cursor:
					cursor.close()

		threads = [
			threading.Thread(target=attempt, args=("payment-a",), daemon=True),
			threading.Thread(target=attempt, args=("payment-b",), daemon=True),
		]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join(timeout=10)
		if any(thread.is_alive() for thread in threads):
			raise AssertionError("Concurrent database transactions did not finish")

		final = frappe.db.sql(
			f"""SELECT
				(SELECT outstanding FROM {quoted_table} WHERE record_id = 'invoice') AS outstanding,
				COALESCE(SUM(allocated), 0) AS allocated_total,
				SUM(record_id LIKE 'payment-%') AS payment_rows
			FROM {quoted_table}""",
			as_dict=True,
		)[0]
		submitted = [row for row in results if row["status"] == "submitted"]
		rejected = [row for row in results if row["status"] == "rejected"]
		connection_ids = {row.get("connection_id") for row in results}
		if len(connection_ids) != 2 or len(submitted) != 1 or len(rejected) != 1:
			raise AssertionError(f"Expected one submit and one rejection on independent connections: {results}")
		if float(final.outstanding) != 0 or float(final.allocated_total) != 100:
			raise AssertionError(f"Outstanding/allocation did not reconcile: {final}")
		if int(final.payment_rows) != 1:
			raise AssertionError(f"Duplicate allocation row was created: {final}")
		if max(row["lock_wait_seconds"] for row in results) < 0.5:
			raise AssertionError(f"The competing transaction did not demonstrably wait for the row lock: {results}")
		flags = frappe.db.sql(
			"""SELECT
				COALESCE(SUM(enable_catalog_management), 0) AS catalog,
				COALESCE(SUM(enable_purchases), 0) AS purchases,
				COALESCE(SUM(enable_supplier_payments), 0) AS supplier_payments
			FROM `tabPOS Settings`""",
			as_dict=True,
		)[0]
		if any(int(value) for value in flags.values()):
			raise AssertionError(f"Management flags are not OFF: {flags}")
		print({"transactions": sorted(results, key=lambda row: row["payment"]), "final": dict(final), "flags": dict(flags)})
		return 0
	except Exception:
		traceback.print_exc()
		return 1
	finally:
		for connection in connections:
			connection.close()
		try:
			frappe.db.sql(f"DROP TABLE IF EXISTS {quoted_table}")
			frappe.db.commit()
		finally:
			frappe.destroy()


if __name__ == "__main__":
	sys.exit(run())
