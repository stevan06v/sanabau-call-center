import time

from libs.models import VapiCallReport
from libs.sheets import get_records_from_worksheet
from vapi import Vapi
from libs.sheets import sheet
from keys import VAPI_API_TOKEN, PHONE_NUMBER_ID, ASSISTANT_ID, SHEETS_WEBHOOK_URL, SHEETS_GID
import requests


BATCH_COUNT = 2  # max allowed size: 10 -> because of VAPI-policy
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
        batch = phone_numbers
    else:
        batch = phone_numbers[:BATCH_COUNT]

    make_outbound_chunk(batch)


def classify_call(ended_reason: str) -> str:
    success_reasons = {
        "assistant-ended-call",
        "assistant-ended-call-after-message-spoken",
        "assistant-ended-call-with-hangup-task",
        "assistant-forwarded-call",
        "assistant-said-end-call-phrase",
        "customer-ended-call",
        "vonage-completed",
        "voicemail",
    }

    retry_reasons = {
        "customer-busy",
        "customer-did-not-answer",
        "customer-did-not-give-microphone-permission",
        "call.in-progress.error-assistant-did-not-receive-customer-audio",
        "phone-call-provider-closed-websocket",
        "phone-call-provider-bypass-enabled-but-no-call-received",
        "twilio-failed-to-connect-call",
        "twilio-reported-customer-misdialed",
        "vonage-disconnected",
        "vonage-failed-to-connect-call",
        "vonage-rejected",
        "call.in-progress.error-sip-telephony-provider-failed-to-connect-call",
        "call.forwarding.operator-busy",
        "silence-timed-out",
    }

    if ended_reason in success_reasons:
        return "success"
    elif ended_reason in retry_reasons:
        return "retry"
    else:
        return "error"


def update_record(vapi_call_report: VapiCallReport):
    header = sheet.row_values(1)

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

    records = get_records_from_worksheet("Tabellenblatt1")

    for idx, record in enumerate(records, start=2):
        if str(record.get("formatted_phone")) == str(vapi_call_report.customer.number).replace('+', ''):
            sheet.update_cell(idx, record_col_index.get("call_id"), vapi_call_report.call.id)
            sheet.update_cell(idx, record_col_index.get("name"), vapi_call_report.analysis.structuredData.name)
            sheet.update_cell(idx, record_col_index.get("call_date"), str(vapi_call_report.startedAt))
            sheet.update_cell(idx, record_col_index.get("status"), str(vapi_call_report.analysis.structuredData.status))
            sheet.update_cell(idx, record_col_index.get("called"), "CALLED")
            sheet.update_cell(idx, record_col_index.get("email"), vapi_call_report.analysis.structuredData.email)
            sheet.update_cell(idx, record_col_index.get("email_sent"), "")
            sheet.update_cell(idx, record_col_index.get("branche"), vapi_call_report.analysis.structuredData.branche)
            sheet.update_cell(idx, record_col_index.get("summary"), vapi_call_report.summary)
            sheet.update_cell(idx, record_col_index.get("duration"), str(vapi_call_report.durationMinutes))
            sheet.update_cell(idx, record_col_index.get("fax"), vapi_call_report.analysis.structuredData.fax)
            sheet.update_cell(
                idx,
                record_col_index.get("transcript"),
                f'=HYPERLINK("{vapi_call_report.stereoRecordingUrl}";"Recording")'
            )
            sheet.update_cell(idx, record_col_index.get("classification"), "")
            print(f"Telefonnummer {vapi_call_report.customer.number} wurde auf '{"CALLED"}' aktualisiert (Zeile {idx})")
            break
    else:
        print("no match found!")


