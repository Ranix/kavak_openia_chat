# python
import unittest
import json
from unittest.mock import patch
import pandas as pd

# Absolute import per project namespace package
import app.services.car_logic as car_logic
from app.services.car_logic import search_cars, calculate_financing

class TestCarLogic(unittest.TestCase):
    def setUp(self):
        # Build a deterministic in-memory catalog
        rows = [
            {"make": "Chevrolet", "model": "Onix", "price": 250000, "km": 50000},
            {"make": "Chevrolet", "model": "Aveo", "price": 280000, "km": 30000},
            {"make": "Toyota", "model": "Corolla", "price": 350000, "km": 40000},
            {"make": "Ford", "model": "Fiesta", "price": 150000, "km": 70000},
        ]
        test_df = pd.DataFrame(rows)
        # Inject into module-level df_cars used by functions
        car_logic.df_cars = test_df

    def _extract_one_side_effect(self, query, choices, *args, **kwargs):
        # Simple heuristic: if choices are makes, return Chevrolet for "Chebys"
        choices_list = list(choices)
        if set(choices_list) & {"Chevrolet", "Toyota", "Ford"}:
            # matching makes
            if "cheb" in str(query).lower() or "chev" in str(query).lower():
                return ("Chevrolet", 90)
            # fallback: return first choice with low score
            return (choices_list[0], 50)
        else:
            # matching models: map queries to models
            q = str(query).lower()
            for model in choices_list:
                if q in str(model).lower() or str(model).lower().startswith(q):
                    return (model, 90)
            return (choices_list[0], 50)

    def test_search_cars_make_fuzzy_match_success(self):
        with patch("app.services.car_logic.process.extractOne", side_effect=self._extract_one_side_effect):
            result_json = search_cars(make="Chebys")
            data = json.loads(result_json)
            # Expect two Chevrolet entries
            self.assertIsInstance(data, list)
            models = {item["model"] for item in data}
            self.assertEqual(len(data), 2)
            self.assertTrue({"Onix", "Aveo"}.issubset(models))

    def test_search_cars_make_fuzzy_match_low_score(self):
        # Force low score for make matching
        def low_score(query, choices, *a, **k):
            return (choices[0], 50)
        with patch("app.services.car_logic.process.extractOne", side_effect=low_score):
            result_json = search_cars(make="Chebys")
            data = json.loads(result_json)
            self.assertIsInstance(data, dict)
            self.assertIn("error", data)
            self.assertIn("Make", data["error"])

    def test_search_cars_filters_price_and_km(self):
        # Use high scoring make match
        with patch("app.services.car_logic.process.extractOne", side_effect=self._extract_one_side_effect):
            # Filter to only include cars priced <= 260000 and km <= 60000 -> should include Onix only
            result_json = search_cars(make="Chebys", max_price=260000, max_km=60000)
            data = json.loads(result_json)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["model"], "Onix")

    def test_calculate_financing_valid(self):
        result_json = calculate_financing(100000, 20000, 4)
        data = json.loads(result_json)
        self.assertIn("loan_amount", data)
        self.assertEqual(data["loan_amount"], 80000)
        self.assertEqual(data["term_years"], 4)
        self.assertIn("monthly_payment", data)
        self.assertIsInstance(data["monthly_payment"], (int, float))

    def test_calculate_financing_invalid_term(self):
        result_json = calculate_financing(50000, 5000, 2)
        data = json.loads(result_json)
        self.assertIsInstance(data, dict)
        self.assertIn("error", data)
        self.assertIn("between 3 and 6", data["error"])

    def test_calculate_financing_down_payment_covers_price(self):
        result_json = calculate_financing(30000, 30000, 4)
        data = json.loads(result_json)
        self.assertIsInstance(data, dict)
        self.assertIn("message", data)
        self.assertIn("No financing needed", data["message"] or "")

if __name__ == "__main__":
    unittest.main()