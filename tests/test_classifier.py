import unittest
from agents.classifier_agent import ClassifierAgent

class TestClassifierAgent(unittest.TestCase):

    def setUp(self):
        self.classifier = ClassifierAgent()

    def test_classify_pdf(self):
        input_data = "sample.pdf" # Sample PDF input (in practice, this would be the content of a PDF file) 
        result = self.classifier.classify(input_data)
        self.assertEqual(result['format'], 'PDF')
        self.assertIn('intent', result)

    def test_classify_json(self):
        input_data = '{"key": "value"}'  # Sample JSON input
        result = self.classifier.classify(input_data)
        self.assertEqual(result['format'], 'JSON')
        self.assertIn('intent', result)

    def test_classify_email(self):
        input_data = "From: sender@example.com\nSubject: Test Email\n\nThis is a test email."  # Sample email content
        result = self.classifier.classify(input_data)
        self.assertEqual(result['format'], 'Email')
        self.assertIn('intent', result)

    def test_invalid_input(self):
        input_data = "This is an invalid input."
        with self.assertRaises(ValueError):
            self.classifier.classify(input_data)

if __name__ == '__main__':
    unittest.main()