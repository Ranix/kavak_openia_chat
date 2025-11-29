import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

from app.schemas import chat
from app.services.llm_orchestration import run_agent

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = FastAPI()

@app.post("/chat", response_model=chat.ChatResponse)
async def chat_endpoint(request: Request) -> PlainTextResponse:
    """Process incoming Twilio webhook messages and return an XML TwiML response.

    This endpoint receives an incoming webhook from Twilio containing SMS
    information such as sender phone number and message body. It forwards the
    message to the LLM orchestration agent and returns the generated reply
    wrapped in Twilio's required XML (TwiML).

    Args:
        request (Request): The incoming FastAPI request containing form-encoded
            Twilio webhook fields.

    Returns:
        PlainTextResponse: A TwiML XML response containing the bot's message.

    Raises:
        HTTPException: If an unexpected error occurs while processing the request.
    """
        
    try:
        data = await request.form()
        number = data.get("From")
        body = data.get("Body")
        logger.info(f"Incoming message | From: {number} | Body: {body}")

        # LLM Call
        bot_reply = run_agent(number, body)
        logger.info(f"Generated bot reply: {bot_reply.response}")

        # Twilio response
        resp = MessagingResponse()
        resp.message(bot_reply.response)
        twiml_xml = str(resp)
        logger.info("Returning TwiML XML response")

        return PlainTextResponse(content=twiml_xml, media_type="application/xml")
    except Exception as exc:
        logger.error(f"Unhandled error in /chat endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))