import time
import threading
from libs.helpers import send_html_email, save_temp_html, render_notification_company, render_confirmation_client, \
    classify_call
from libs.models import VapiCallReport
from libs.sheets import get_records_from_worksheet
from vapi import Vapi
from libs.sheets import sheet
from keys import VAPI_API_TOKEN, PHONE_NUMBER_ID, ASSISTANT_ID, SHEETS_WEBHOOK_URL, SHEETS_GID, SMTP_SERVER, SMTP_PORT, \
    SMTP_EMAIL, SMTP_PASSWORD
import requests


BATCH_COUNT = 2  # max allowed size: 10 -> VAPI-policy
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
    print("\n==============================================\n")
    print(f"Removing call_id {call_id} from batch list:")
    print(CURRENT_BATCH_LIST)
    print("\n==============================================\n")

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
        #print("Batch initiated, response:", resp)
        CURRENT_BATCH_LIST = [call.id for call in resp.results]
        return resp
    except Exception as e:
        print(f"Error initiating outbound call: {e}")


def get_uncalled_records():
    uncalled_records = []
    records = get_records_from_worksheet("Template")
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
        batch = phone_numbers
    else:
        batch = phone_numbers[:BATCH_COUNT]

    make_outbound_chunk(batch)


def update_record(vapi_call_report: VapiCallReport):
    header = sheet.row_values(1)

    email_sent = vapi_call_report.analysis.structuredData.status in ["INTERESSIERT", "SEHR INTERESSIERT"]

    record_col_index = {
        "call_id": header.index("call_id") + 1,
        "name": header.index("name") + 1,
        "call_date": header.index("call_date") + 1,
        "called": header.index("called") + 1,
        "email": header.index("email") + 1,
        "email_sent": header.index("email_sent") + 1,
        "status": header.index("status") + 1,
        "branche": header.index("branche") + 1,
        "summary": header.index("summary") + 1,
        "duration": header.index("duration") + 1,
        "fax": header.index("fax") + 1,
        "transcript": header.index("transcript") + 1,
        "classification": header.index("classification") + 1,
    }

    customer_number = None
    if getattr(vapi_call_report, "customer", None) and getattr(vapi_call_report.customer, "number", None):
        customer_number = str(vapi_call_report.customer.number).replace("+", "")
    elif getattr(vapi_call_report.analysis.structuredData, "phone", None):
        customer_number = str(vapi_call_report.analysis.structuredData.phone).replace("+", "")

    if not customer_number:
        print("⚠️ Keine Telefonnummer im Report gefunden – kein Update möglich.")
        return

    if vapi_call_report.analysis.successEvaluation:
        classification = classify_call(vapi_call_report.endedReason)
    else:
        classification = "retry"

    records = get_records_from_worksheet("Template")

    for idx, record in enumerate(records, start=2):
        if str(record.get("formatted_phone")) == customer_number:
            sheet.update_cell(idx, record_col_index.get("call_id"), vapi_call_report.call.id)
            sheet.update_cell(idx, record_col_index.get("name"), vapi_call_report.analysis.structuredData.name)
            sheet.update_cell(idx, record_col_index.get("call_date"), str(vapi_call_report.startedAt))
            sheet.update_cell(idx, record_col_index.get("status"), str(vapi_call_report.analysis.structuredData.status))
            sheet.update_cell(idx, record_col_index.get("called"), "CALLED")
            sheet.update_cell(idx, record_col_index.get("email"), vapi_call_report.analysis.structuredData.email)
            sheet.update_cell(idx, record_col_index.get("email_sent"), "SENT" if email_sent else "NOT SENT")
            sheet.update_cell(idx, record_col_index.get("branche"), vapi_call_report.analysis.structuredData.branche)
            sheet.update_cell(idx, record_col_index.get("summary"), vapi_call_report.summary)
            sheet.update_cell(idx, record_col_index.get("duration"), str(vapi_call_report.durationMinutes))
            sheet.update_cell(idx, record_col_index.get("fax"), vapi_call_report.analysis.structuredData.fax)
            sheet.update_cell(
                idx,
                record_col_index.get("transcript"),
                f'=HYPERLINK("{vapi_call_report.stereoRecordingUrl}";"Recording")'
            )
            sheet.update_cell(idx, record_col_index.get("classification"), classification)
            print(f"Telefonnummer {vapi_call_report.customer.number} wurde auf 'CALLED' aktualisiert (Zeile {idx})")
            break
    else:
        print("no match found!")

    def _job():
        status = getattr(
            getattr(vapi_call_report.analysis, "structuredData", None),
            "status",
            None
        )

        if status in ["INTERESSIERT", "SEHR INTERESSIERT"]:
            success = send_html_email(
                smtp_server="78.46.226.32",
                smtp_port=55587,
                sender_email="info@homa-bau.com",
                sender_password="8@B%eD>AGtd8LM:",
                recipient_email="info@homa-bau.com",
                subject="Neuer Interessent gemeldet",
                content=save_temp_html(render_notification_company(vapi_call_report))
            )
            print(f"===Email sent to info@homa-bau.com: {success}===")

            try:
                recipient = getattr(
                    getattr(vapi_call_report.analysis, "structuredData", None),
                    "email",
                    None
                )
                if recipient:
                    send_html_email(
                        smtp_server="78.46.226.32",
                        smtp_port=55587,
                        sender_email="info@homa-bau.com",
                        sender_password="8@B%eD>AGtd8LM:",
                        recipient_email=recipient,
                        subject="Sana Bau GmbH — Bestätigung",
                        content=save_temp_html(render_confirmation_client(vapi_call_report))
                    )
            except Exception as e:
                print(f"Error sending confirmation email: {e}")

    threading.Thread(target=_job, daemon=True).start()


