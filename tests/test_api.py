"""
Unit tests for the Flask API
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
import torch

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.app import app


class TestAPI(unittest.TestCase):
    """Test the Flask API endpoints"""
    
    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('api.app.send_from_directory')
    def test_index_route(self, mock_send):
        """Test the index route"""
        # Set up mock
        mock_send.return_value = "HTML content"
        
        # Make a request to the index route
        response = self.app.get('/')
        
        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        
        # Check that send_from_directory was called with the right arguments
        mock_send.assert_called_once_with(app.static_folder, "index.html")
        
    @patch('api.app.send_from_directory')
    def test_static_route(self, mock_send):
        """Test the static file route"""
        # Set up mock
        mock_send.return_value = "Static content"
        
        # Make a request to a static file
        response = self.app.get('/styles.css')
        
        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        
        # Check that send_from_directory was called with the right arguments
        mock_send.assert_called_once_with(app.static_folder, "styles.css")
        
    @patch('api.app.tokenizer')
    @patch('api.app.model')
    @patch('torch.no_grad')
    def test_generate_route(self, mock_no_grad, mock_model, mock_tokenizer):
        """Test the generate route"""
        # Set up mocks
        mock_input_ids = torch.tensor([[1, 2, 3]])
        mock_tokenizer.encode.return_value = mock_input_ids
        
        mock_output = torch.tensor([[1, 2, 3, 4, 5, 6]])
        mock_model.generate.return_value = mock_output
        
        mock_tokenizer.decode.return_value = "Generated response"
        
        # Mock torch.no_grad to do nothing
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=None)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_no_grad.return_value = mock_context
        
        # Make a request to the generate route
        response = self.app.post('/generate', 
                                json={'prompt': 'Test prompt'})
        
        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertEqual(data['response'], "Generated response")
        
        # Check that tokenizer.encode was called
        mock_tokenizer.encode.assert_called_once()
        
        # Check that model.generate was called
        mock_model.generate.assert_called_once()
        
        # Check that tokenizer.decode was called
        mock_tokenizer.decode.assert_called_once()
        
    def test_generate_route_no_prompt(self):
        """Test the generate route with no prompt"""
        # Create a patch for the model and tokenizer
        with patch('api.app.tokenizer') as mock_tokenizer, \
             patch('api.app.model') as mock_model, \
             patch('torch.no_grad'):
            
            # Set up mocks
            mock_input_ids = torch.tensor([[1, 2, 3]])
            mock_tokenizer.encode.return_value = mock_input_ids
            
            mock_output = torch.tensor([[1, 2, 3, 4, 5, 6]])
            mock_model.generate.return_value = mock_output
            
            mock_tokenizer.decode.return_value = "Generated response"
            
            # Make a request to the generate route with empty JSON
            response = self.app.post('/generate', json={})
            
            # Check that the response is correct
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('response', data)
            
            # Check that tokenizer.encode was called with an empty prompt
            args, _ = mock_tokenizer.encode.call_args
            self.assertIn("User: \nBot:", args[0])
            
    def test_health_check(self):
        """Test the health check endpoint"""
        # Make a request to the health check endpoint
        response = self.app.get('/health')
        
        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('model', data)
        self.assertIn('version', data)


if __name__ == '__main__':
    unittest.main()
