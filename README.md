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

## Sources
* VAPI-API https://docs.vapi.ai/quickstart/phone
