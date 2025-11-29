import json
import logging

from openai import OpenAI

from app.core import config, llm_promp
from app.schemas import chat
from app.services import car_logic, tools_shema

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

client = OpenAI(api_key=config.OPENAI_API_KEY)

AVAILABLE_FUNCTIONS = {
    "search_cars": car_logic.search_cars,
    "calculate_financing": car_logic.calculate_financing
}

# STATE MANAGEMENT (In-Memory for Demo)          --- In production, replace this with Redis ---
SESSIONS = {}

def run_agent(user_number: str, user_message: str) -> chat.ChatResponse:
    """
    Run the conversational agent for a specific user and incoming message.

    This function manages session history, sends prompts to the OpenAI model,
    processes optional tool calls returned by the model, executes Python
    functions when requested, and returns the model's final response.

    Arguments:
        user_number (str): Unique identifier for the user or session.
        user_message (str): Natural language input message from the user.

    Returns:
        chat.ChatResponse: Object containing the assistant's generated text
        response, after tool use (if any) and final LLM pass.
    """
    
    # Initialize or Retrieve History
    if user_number not in SESSIONS:
        logger.debug(f"No existing session. Creating new session for {user_number}")
        SESSIONS[user_number] = [{"role": "system", "content": llm_promp.SYSTEM_INSTRUCTIONS}]
    
    messages = SESSIONS[user_number]
    messages.append({"role": "user", "content": user_message})
    logger.debug(f"Current message history for {user_number}: {messages}")

    #  OpenAI Call
    logger.info("Sending request to OpenAI (first pass)")
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools_shema.TOOLS,
            tool_choice="auto"
        )
    msg = response.choices[0].message
    logger.debug(f"OpenAI raw response: {msg}")

    # Handle Tool Calls
    if msg.tool_calls:
        logger.info(f"Tool calls detected: {msg.tool_calls}")
        messages.append(msg)
        
        for tool_call in msg.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            logger.info(f"Executing tool: {function_name} with args: {function_args}")

            if function_name in AVAILABLE_FUNCTIONS:
                try:
                    # Execute Python function
                    function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
                    logger.debug(f"Tool response: {function_response}")
                except Exception as e:
                    logger.error(f"Error executing tool {function_name}: {e}")
                    function_response = {"error": str(e)}
                
                messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })
                
        # Second OpenAI Call: Get final natural language response
        logger.info("Sending request to OpenAI (second pass for natural response)")
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        final_msg = final_response.choices[0].message.content
        logger.info(f"Final agent response: {final_msg}")

        messages.append({"role": "assistant", "content": final_msg})
        return chat.ChatResponse(response=final_msg)

    else:
        # No tool call needed (Standard conversation)
        logger.info(f"No tool call needed. Final response: {msg.content}")
        messages.append({"role": "assistant", "content": msg.content})
        return chat.ChatResponse(response=msg.content)