from fastapi import FastAPI, Request
from vapi import Vapi
from libs.services import start_campaign, get_uncalled_records
from keys import VAPI_API_TOKEN, PHONE_NUMBER_ID, ASSISTANT_ID
from libs.services import remove_call_id,get_current_batch_list, send_webhook_notify

app = FastAPI()

client = Vapi(token=VAPI_API_TOKEN)

#@app.get("/start-campaign")
#def main():
#    make_outbound_call("+436643279885")
#    return {"success": "True"}


@app.post("/vapi/log")
async def log_call(request: Request):
    data = await request.json()
    print(data)

@app.post("/call-status-update")
async def log_call(request: Request):
    data = await request.json()
    signature = request.headers.get("X-Vapi-Signature")
    if signature != "your-secret-token":
        return {"error": "unauthorized"}, 401
    msg = data.get("message", {})
    if msg.get("type") == "end-of-call-report":
        print(msg)
        call = msg.get("call", {})

        current_call_id = call.get("id")
        remove_call_id(current_call_id)

        if not get_current_batch_list(): # if empty = true
            send_webhook_notify()

    return {"success": True}


@app.get("/")
def read_root():
    send_webhook_notify()
    #start_campaign()
    return {"Hello": "World"}


@app.get("/get-uncalled")
def read_root():
    get_uncalled_records()
    return {"status": True}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"sheet_count": item_id}
