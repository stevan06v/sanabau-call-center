# sanabau-call-center
About
A vapi script processing lists of bavarian construction companies and calling them with an ai agent to generate leads / create business cooperations.

## Workflow
1. Read pending leads from sheet
2. Call via Vapi REST SDK
4. Assistant triggers Sheets append tool (REST-Route)
5. Function responds to Sheets tool to commit data
6. Backend updates original sheet "called" status via API
7. Repeat for next lead

## Startup

1. Enter Venv
```sh
poetry shell
poetry install --no-root
```

2. Start webserver and forward
```sh
uvicorn main:app --reload
ngrok http 127.0.0.1:8000
```

## Sources
* VAPI-API https://docs.vapi.ai/quickstart/phone
* BATCH CALLING: https://youtu.be/aAOv4OxLgmk?si=URc_oDfxL2a6mWDW