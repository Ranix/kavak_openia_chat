import json
import logging

import pandas as pd
from thefuzz import process

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Data Loading 
try:
    df_cars = pd.read_csv("data/vehicles.csv")
    logger.info("Car catalog loaded successfully.")
except FileNotFoundError:
    logger.error("Error: vehicles.csv not found. Please ensure the file exists.")
    df_cars = pd.DataFrame()


def search_cars(make: str = None, model: str = None, max_price: int = None, max_km: int = None) -> dict:
    """Search the car catalog using make, model, price, and mileage filters.
    Fuzzy matching is applied to handle spelling errors.

    Args:
        make (str, optional): Car manufacturer to search for.
        model (str, optional): Car model to search for.
        max_price (int, optional): Maximum allowed price.
        max_km (int, optional): Maximum allowed mileage.

    Returns:
        str: JSON-formatted list of matching cars or an error message.
    """
    results = df_cars.copy()

    # Fuzzy match: Make
    if make:
        unique_makes = df_cars['make'].unique()
        best_match, score = process.extractOne(make, unique_makes)
        logger.info(f"Fuzzy match for make '{make}' → '{best_match}' (score={score})")

        if score > 70:  # Threshold for fuzzy match
            results = results[results['make'] == best_match]
        else:
            logger.warning(f"Make fuzzy match score too low: {score}")
            return json.dumps({"error": f"Make '{make}' not found. Did you mean {best_match}?"})

    # Fuzzy match: Model 
    if model:
        possible_models = results['model'].unique() if not results.empty else df_cars['model'].unique()
        best_match_model, score_model = process.extractOne(model, possible_models)
        logger.info(
            f"Fuzzy match for model '{model}' → '{best_match_model}' (score={score_model})"
        )
        
        if score_model > 70:
            results = results[results['model'] == best_match_model]
        else:
            logger.warning(f"Model fuzzy match score too low: {score_model}")
            return json.dumps({"error": f"Model '{model}' not found in our current inventory."})

    # Filters
    if max_price:
        results = results[results['price'] <= max_price]
        logger.info(f"Applied max_price filter: {max_price}")
    
    if max_km:
        results = results[results['km'] <= max_km]
        logger.info(f"Applied max_km filter: {max_km}")

    if results.empty:
        logger.info("No cars found matching the search criteria.")
        return json.dumps({"message": "No cars found matching those preferences."})

    # Convert to list of dicts for the LLM
    return results.to_json(orient="records")


def calculate_financing(car_price: float, down_payment: float, term_years: int) -> str:
    """Calculate the monthly financing payment using an amortization formula.

    Interest rate is fixed at 10% annually. Valid financing terms range from
    3 to 6 years.

    Args:
        car_price (float): Total price of the car.
        down_payment (float): Initial amount paid upfront.
        term_years (int): Financing term in years (3–6 valid).

    Returns:
        str: JSON-formatted financing breakdown including monthly payment.
    """
    if term_years < 3 or term_years > 6:
        logger.error(f"Invalid financing term: {term_years}")
        return json.dumps({"error": "Financing term must be between 3 and 6 years."})
    
    if down_payment >= car_price:
        logger.info("Down payment covers full price — no financing needed.")
        return json.dumps({"message": "Down payment covers the full price. No financing needed!"})

    principal = car_price - down_payment
    annual_rate = 0.10
    monthly_rate = annual_rate / 12
    num_months = term_years * 12

    # Amortization Formula: M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1 ]
    if principal <= 0:
        logger.error(f"Invalid principal calculation: {principal}")
        return json.dumps({"error": "Invalid principal amount."})

    numerator = monthly_rate * ((1 + monthly_rate) ** num_months)
    denominator = ((1 + monthly_rate) ** num_months) - 1
    monthly_payment = principal * (numerator / denominator)

    logger.info(f"Monthly payment calculated: {round(monthly_payment, 2)}")

    return json.dumps({
        "car_price": car_price,
        "down_payment": down_payment,
        "loan_amount": principal,
        "term_years": term_years,
        "monthly_payment": round(monthly_payment, 2),
        "interest_rate": "10%"
    })