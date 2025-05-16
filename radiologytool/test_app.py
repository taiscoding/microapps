import unittest
from app import app, translate_radiology_impression
from utils import identify_medical_terms, get_simplified_explanation

class TestRadiologyTranslator(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_page(self):
        """Test that the home page loads correctly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_translation_endpoint_with_empty_input(self):
        """Test that the translation endpoint handles empty inputs properly"""
        response = self.app.post('/translate', data={'impression': ''})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_medical_term_identification(self):
        """Test that medical terms are correctly identified"""
        test_text = "Patient exhibits hypertension and mild cardiac issues"
        identified_terms = identify_medical_terms(test_text)
        self.assertIn('hypertension', identified_terms)
        self.assertIn('cardiac', identified_terms)
    
    def test_medical_term_explanation(self):
        """Test that medical terms are correctly explained"""
        explanation = get_simplified_explanation('hypertension')
        self.assertEqual(explanation, 'high blood pressure')

if __name__ == '__main__':
    unittest.main() 