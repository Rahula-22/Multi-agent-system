import unittest
from agents.json_agent import JSONAgent

class TestJSONAgent(unittest.TestCase):

    def setUp(self):
        self.agent = JSONAgent()

    def test_valid_json(self):
        input_data = {
            "name": "Sample",
            "amount": 100,
            "currency": "USD"
        }
        expected_output = {
            "name": "Sample",
            "amount": 100,
            "currency": "USD",
            "status": "valid"
        }
        output = self.agent.process(input_data)
        self.assertEqual(output, expected_output)

    def test_invalid_json(self):
        input_data = {
            "name": "Sample",
            "amount": None  # Invalid amount
        }
        expected_output = {
            "name": "Sample",
            "amount": None,
            "status": "invalid",
            "error": "Missing required field: amount"
        }
        output = self.agent.process(input_data)
        self.assertEqual(output, expected_output)

    def test_anomalies_in_json(self):
        input_data = {
            "name": "Sample",
            "amount": 100,
            "currency": "XYZ"  # Anomaly in currency
        }
        expected_output = {
            "name": "Sample",
            "amount": 100,
            "currency": "XYZ",
            "status": "valid",
            "anomalies": ["Unknown currency: XYZ"]
        }
        output = self.agent.process(input_data)
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()