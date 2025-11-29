import unittest
from types import SimpleNamespace
from fastapi.testclient import TestClient
from unittest.mock import patch

# relative import of the app and the function under test (per requirements)
from app.main import app, chat_endpoint

class TestChatEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.url = "/chat"
        self.form_data = {"From": "+15551234567", "Body": "Hello bot"}

    def test_chat_endpoint_success_returns_twiml(self):
        # Arrange: patch run_agent to return an object with a `.response` attribute
        fake_reply = SimpleNamespace(response="Hello from agent")
        with patch("app.main.run_agent", return_value=fake_reply):
            # Act
            resp = self.client.post(self.url, data=self.form_data)
            # Assert
            self.assertEqual(resp.status_code, 200)
            # FastAPI TestClient returns text for xml responses
            self.assertIn("application/xml", resp.headers.get("content-type", ""))
            # TwiML message element should include the response text
            self.assertIn("<Message>Hello from agent</Message>", resp.text)

    def test_chat_endpoint_handles_run_agent_exception(self):
        # Arrange: patch run_agent to raise
        def raise_exc(number, body):
            raise Exception("boom")
        with patch("app.main.run_agent", side_effect=raise_exc):
            # Act
            resp = self.client.post(self.url, data=self.form_data)
            # Assert: HTTPException in endpoint should produce a 500 response
            self.assertEqual(resp.status_code, 500)
            json_body = resp.json()
            # FastAPI returns {"detail": "..."} for HTTPException
            self.assertIn("detail", json_body)
            self.assertIn("boom", str(json_body["detail"]))

if __name__ == "__main__":
    unittest.main()