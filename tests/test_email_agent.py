import unittest
from agents.email_agent import EmailParserAgent

class TestEmailParserAgent(unittest.TestCase):

    def setUp(self):
        self.agent = EmailParserAgent()

    def test_extract_sender(self):
        email_body = "From: John Doe <john@example.com>\nSubject: Request for Quotation\n\nHello, I would like to request a quotation for your services."
        result = self.agent.extract_sender(email_body)
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['email'], 'john@example.com')

    def test_extract_intent(self):
        email_body = "From: Jane Smith <jane@example.com>\nSubject: Complaint\n\nI have a complaint regarding my last order."
        result = self.agent.extract_intent(email_body)
        self.assertEqual(result, 'Complaint')

    def test_extract_urgency(self):
        email_body = "From: Mark Brown <mark@example.com>\nSubject: Urgent: Invoice Needed\n\nPlease send me the invoice as soon as possible."
        result = self.agent.extract_urgency(email_body)
        self.assertTrue(result)

    def test_format_crm_record(self):
        email_body = "From: Alice Johnson <alice@example.com>\nSubject: RFQ\n\nI am interested in your products."
        sender_info = self.agent.extract_sender(email_body)
        intent = self.agent.extract_intent(email_body)
        urgency = self.agent.extract_urgency(email_body)
        crm_record = self.agent.format_crm_record(sender_info, intent, urgency)
        self.assertIn('sender', crm_record)
        self.assertIn('intent', crm_record)
        self.assertIn('urgency', crm_record)

if __name__ == '__main__':
    unittest.main()