from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.conversation import handle_message

app = FastAPI()

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    user_msg = form.get("Body")
    user_phone = form.get("From")

    print("Message:", user_msg)
    print("From:", user_phone)

    reply = handle_message(user_phone, user_msg)
    print("Reply generated:", reply)

    resp = MessagingResponse()
    resp.message(reply)
    return Response(content=str(resp), media_type="application/xml")
