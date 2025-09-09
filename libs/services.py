import time
from libs.sheets import get_records_from_worksheet
from vapi import Vapi
from libs.sheets import sheet
from keys import VAPI_API_TOKEN, PHONE_NUMBER_ID, ASSISTANT_ID, SHEETS_WEBHOOK_URL, SHEETS_GID
import requests


BATCH_COUNT = 1
CURRENT_BATCH_LIST = []
CURRENT_UNCALLED_COUNT = 0


try:
    client = Vapi(token=VAPI_API_TOKEN)
    print(VAPI_API_TOKEN)
except Exception as e:
    print("VAPI API TOKEN not provided!")

UNCALLED_RECORDS = list()


def remove_call_id(call_id: str):
    global CURRENT_BATCH_LIST
    CURRENT_BATCH_LIST.remove(call_id)


def get_current_batch_list():
    global CURRENT_BATCH_LIST
    return CURRENT_BATCH_LIST


def send_webhook_notify():
    requests.post(SHEETS_WEBHOOK_URL, json={"finished": True})


def make_outbound_chunk(batch):
    global CURRENT_BATCH_LIST
    print(batch)
    try:
        resp = client.calls.create(
            assistant_id=ASSISTANT_ID,
            phone_number_id=PHONE_NUMBER_ID,
            customers=[{"number": num} for num in batch]
        )
        print("Batch initiated, response:", resp)
        CURRENT_BATCH_LIST = [call.id for call in resp.results]
        return resp
    except Exception as e:
        print(f"Error initiating outbound call: {e}")


def get_uncalled_records():
    uncalled_records = []
    records = get_records_from_worksheet("Tabellenblatt1")
    for iterator in records:
        if iterator.get("called") == "NOT CALLED":
            uncalled_records.append(iterator)
    return uncalled_records


def start_campaign():
    global CURRENT_UNCALLED_COUNT
    records = get_uncalled_records()

    if not records:
        print("No uncalled records found.")
        return

    phone_numbers = [
        str(f"+{num.get('formatted_phone')}") for num in records
    ]
    print(phone_numbers)

    CURRENT_UNCALLED_COUNT = len(records)
    if CURRENT_UNCALLED_COUNT < BATCH_COUNT: # if amount of remaining uncalled < batch_size -> take what is left
        batch = records
    else:
        batch = phone_numbers[:BATCH_COUNT]

    make_outbound_chunk(batch)


def update_called_status_by_phone(phone_number: str):
    header = sheet.row_values(1)
    called_col_index = header.index("called") + 1
    records = get_records_from_worksheet("Tabellenblatt1")

    print(called_col_index)

    for idx, record in enumerate(records, start=2):
        if str(record.get("formatted_phone")) == str(phone_number).replace('+', ''):
            sheet.update_cell(idx, called_col_index, "CALLED")
            print(f"Telefonnummer {phone_number} wurde auf '{"CALLED"}' aktualisiert (Zeile {idx})")
            break
    else:
        print("no match found!")


if __name__ == "__main__":

    update_called_status_by_phone("+436604669179".replace('+', ''))
