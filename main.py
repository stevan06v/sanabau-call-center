from fastapi import FastAPI, Request
from vapi import Vapi
from libs.services import start_campaign, get_uncalled_records
from keys import VAPI_API_TOKEN, PHONE_NUMBER_ID, ASSISTANT_ID
from libs.services import remove_call_id, get_current_batch_list, send_webhook_notify, update_called_status_by_phone

app = FastAPI()

client = Vapi(token=VAPI_API_TOKEN)


# @app.get("/start-campaign")
# def main():
#    make_outbound_call("+436643279885")
#    return {"success": "True"}


@app.post("/vapi/log")
async def log_call(request: Request):
    data = await request.json()
    print(data)


@app.post("/gather-caller-data")
async def log_call(request: Request):
    data = await request.json()
    signature = request.headers.get("X-Vapi-Signature")
    if signature != "your-secret-token":
        return {"error": "unauthorized"}, 401
    msg = data.get("message", {})
    if msg.get("type") == "end-of-call-report":
        print("END OF CALL REPORT:")
        print(msg)
        call = msg.get("call", {})

        current_call_id = call.get("id")
        remove_call_id(current_call_id)  # 9 -> 8 -> 7
        # add update phone number here
        customer = call.get("customer", {})
        update_called_status_by_phone("6604669179") # replace with called customer phone number

        '''
        TODO: PARSE the incoming data from msg = data.get("message", {}) out of the string
        and update the sheet(https://docs.google.com/spreadsheets/d/1JXfj7bJ0kUceNgbTMgoSHg34_qb7Z8akd69IaB4lXvQ/edit?gid=0#gid=0) 
        accordingly. make sure to not have then more not_called entries then phonenumbers.
        transcript = should be the link to the audio. the rest of the data could be used from the json
        + import the a new elevenlabs key in VAPI settings for developing purposes. 
        + implement a quick ui with a button which triggers the start_campaign() function.
        + send mail if user is interested
        '''
        # update_called_status_by_phone(customer.get("number"))

        if not get_current_batch_list():  # if empty = true
            start_campaign()
        else:
            print(f'''
            \n\n\n\n\n\n\n\n\n\n\n\n\n
            ENTRIES REMAINING: {get_current_batch_list()}
            ''')

    return {"success": True}


@app.get("/")
def read_root():
    # send_webhook_notify()
    start_campaign()

    return {"success": True}


@app.get("/get-uncalled")
def read_root():
    get_uncalled_records()
    return {"status": True}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"sheet_count": item_id}
