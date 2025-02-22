# invoice_processor.py

import time
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import tempfile

def get_service_account_file_path():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    if credentials_json:
        # Write the JSON content to a temporary file and return its path
        temp = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json")
        temp.write(credentials_json)
        temp.close()
        return temp.name
    else:
        raise Exception("GOOGLE_CREDENTIALS environment variable not set.")

# Configuration constants (adjust paths and credentials as needed)
SERVICE_ACCOUNT_FILE = r"C:\webdriver\myinvoiceautomation-46a38fafc7de.json"
SPREADSHEET_NAME = "WILLONA OMS"
WORKSHEET_NAME = "Narudžbe"
EXPECTED_HEADERS = [ 
    "Broj narudžbe", "Datum", "Ime i prezime kupca", "Adresa", "Grad", "PTT",
    "Telefon", "Šifra", "Barkod", "Naziv proizvoda", "Količina", "Cijena",
    "Popust KM", "Štampa/vez", "Dostava", "Ukupno", "Faktura", "Za naplatu",
    "Napomene", "Dorada", "Status narudžbe"
]
USERNAME = "maloprodaja.k@london.ba"
PASSWORD = "111111"
NEW_INVOICE_URL = "https://apps.billans.ba/VA/WebUI/IzdanRacun/IzdanRacunEdit.aspx?iRacTip=M"

def get_orders_from_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    records = sheet.get_all_records(expected_headers=EXPECTED_HEADERS)
    orders = {}
    for record in records:
        status = record.get("Status narudžbe", "").strip().upper()
        faktura_val = str(record.get("Faktura", "")).strip()
        if status == "SPAKOVANO" and faktura_val == "":
            order_num = str(record["Broj narudžbe"]).strip()
            if order_num not in orders:
                orders[order_num] = {
                    "order_number": order_num,
                    "customer_name": record["Ime i prezime kupca"].strip(),
                    "items": [],
                    "retail": False
                }
            orders[order_num]["items"].append({
                "product_code": str(record["Barkod"]).strip(),
                "quantity": str(record["Količina"]).strip(),
                "discount": str(record["Popust KM"]).strip()
            })
            if str(record.get("Za naplatu", "")).strip() != "":
                orders[order_num]["retail"] = True
    orders = {k: v for k, v in orders.items() if v["retail"]}
    order_list = list(orders.values())
    print(f"Found {len(order_list)} retail orders to process.")
    return sheet, order_list

def mark_order_as_processed(sheet, order_number):
    all_values = sheet.get_all_values()
    header = all_values[0]
    try:
        order_index = header.index("Broj narudžbe")
        status_index = header.index("Status narudžbe")
    except ValueError:
        print("Error: Required header not found.")
        return
    for i, row in enumerate(all_values[1:], start=2):
        if row[order_index].strip() == order_number:
            sheet.update_cell(i, status_index + 1, "SPREMNO")
            print(f"Order {order_number}: row {i} marked as SPREMNO.")

def init_driver():
    options = webdriver.EdgeOptions()
    options.add_argument("start-maximized")
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait

def login(driver, wait):
    driver.get("https://apps.billans.ba/VA/WebUI/Login/LoginUnPw.aspx")
    username_field = wait.until(EC.visibility_of_element_located((By.ID, "ctl04_I_ElektronskaPosta")))
    password_field = driver.find_element(By.ID, "ctl04_I_Geslo")
    username_field.clear()
    username_field.send_keys(USERNAME)
    password_field.clear()
    password_field.send_keys(PASSWORD)
    password_field.send_keys(Keys.RETURN)
    time.sleep(3)

def select_skladiste(wait, driver):
    try:
        skladiste_field = wait.until(EC.visibility_of_element_located((By.ID, "PPC_EPC_DC_I_SkladisceID_text")))
        skladiste_field.clear()
        skladiste_field.send_keys("MP KAKANJ")
        skladiste_field.send_keys(Keys.TAB)
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//table[@id='PPC_EPC_DC_I_SkladisceID_tdata']//tr")) > 0)
        dropdown_table = driver.find_element(By.ID, "PPC_EPC_DC_I_SkladisceID_tdata")
        first_option = dropdown_table.find_element(By.TAG_NAME, "tr")
        first_option.click()
        print("Skladište set to MP KAKANJ.")
    except Exception as e:
        print("Error selecting Skladište: ", e)
    time.sleep(2)

def process_order(order, driver, wait):
    print(f"Processing Order #{order['order_number']} for {order['customer_name']} ...")
    driver.get(NEW_INVOICE_URL)
    customer_field = wait.until(EC.visibility_of_element_located((By.ID, "PPC_EPC_DC_I_Veza")))
    customer_field.clear()
    customer_field.send_keys(order["customer_name"])
    radio_button = driver.find_element(By.ID, "PPC_EPC_DC_I_MestoProdaje_0")
    radio_button.click()
    select_skladiste(wait, driver)
    for idx, item in enumerate(order["items"], start=1):
        print(f"  Adding item {idx} with barcode {item['product_code']}...")
        artikel_field = wait.until(EC.visibility_of_element_located((By.ID, "PPC_EPC_DC_I_ArtikelID_text")))
        artikel_field.clear()
        artikel_field.send_keys(item["product_code"])
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//table[@id='PPC_EPC_DC_I_ArtikelID_tdata']//tr")) > 0)
        try:
            dropdown_table = driver.find_element(By.ID, "PPC_EPC_DC_I_ArtikelID_tdata")
            first_row = dropdown_table.find_element(By.TAG_NAME, "tr")
            first_row.click()
        except Exception as e:
            print("    Error selecting product from dropdown:", e)
        wait.until(lambda d: d.find_element(By.ID, "PPC_EPC_DC_I_Naziv").get_attribute("value") != "")
        quantity_field = wait.until(EC.element_to_be_clickable((By.ID, "PPC_EPC_DC_I_Kolicina")))
        quantity_field.clear()
        quantity_field.send_keys(item["quantity"])
        discount_field = driver.find_element(By.ID, "PPC_EPC_DC_I_Popust")
        discount_field.clear()
        discount_field.send_keys(item["discount"])
        add_button = wait.until(EC.element_to_be_clickable((By.ID, "PPC_EPC_DC_bVnosVrsticeIR")))
        add_button.click()
        wait.until(EC.element_to_be_clickable((By.ID, "PPC_EPC_DC_I_ArtikelID_text")))
        time.sleep(2)
    print(f"  Issuing invoice for Order #{order['order_number']} ...")
    issue_button = wait.until(EC.element_to_be_clickable((By.ID, "PPC_EPC_bIzstavi")))
    issue_button.click()
    print_button = wait.until(EC.element_to_be_clickable((By.ID, "PPC_ctl00_ctl00_lbStampajFiskalniProdaja")))
    print_button.click()
    time.sleep(2)
    print(f"Order #{order['order_number']} processed.\n")

def process_all_orders():
    sheet, order_list = get_orders_from_sheet()
    driver, wait = init_driver()
    login(driver, wait)
    for order in order_list:
        try:
            process_order(order, driver, wait)
            mark_order_as_processed(sheet, order["order_number"])
        except Exception as e:
            print(f"Error processing order {order['order_number']}: {e}")
    driver.quit()
    return "All orders processed."

if __name__ == "__main__":
    result = process_all_orders()
    print(result)
