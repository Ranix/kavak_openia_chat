
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_cars",
            "description": "Searches Kavak inventory. Use when user expresses intent to buy/browse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Car manufacturer (e.g. 'Volkswagen'). Normalize misspellings."},
                    "model": {"type": "string", "description": "Model name."},
                    "max_price": {"type": "number"},
                    "max_km": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_financing",
            "description": "Calculates monthly payment. Do not do math in chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "car_price": {"type": "number"},
                    "down_payment": {"type": "number", "description": "If unspecified, calculate 20% of price."},
                    "term_years": {"type": "integer", "enum": [3, 4, 5, 6]}
                },
                "required": ["car_price", "down_payment", "term_years"]
            }
        }
    }
] 