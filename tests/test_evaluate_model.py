"""
Unit tests for evaluate_model.py
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import torch

# Import the module to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate_model import calculate_perplexity, generate_sample_responses, main


class TestCalculatePerplexity(unittest.TestCase):
    """Test the calculate_perplexity function"""
    
    def setUp(self):
        # Create a temporary file with test data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.temp_file.write("This is a test sentence.\nThis is another test sentence.")
        self.temp_file.close()
        
    def tearDown(self):
        # Remove the temporary file
        os.unlink(self.temp_file.name)
        
    @patch('torch.no_grad')
    def test_calculate_perplexity(self, mock_no_grad):
        """Test that perplexity is calculated correctly"""
        # Create mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Mock the tokenizer to return a tensor
        mock_encodings = MagicMock()
        mock_encodings.input_ids = torch.tensor([[1, 2, 3, 4, 5]])
        mock_tokenizer.return_value = mock_encodings
        
        # Mock the model to return a loss
        mock_outputs = MagicMock()
        mock_outputs.loss = torch.tensor(2.0)  # ln(perplexity) = 2.0, so perplexity = e^2 ≈ 7.39
        mock_model.return_value = mock_outputs
        
        # Mock torch.no_grad to do nothing
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=None)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_no_grad.return_value = mock_context
        
        # Call the function
        perplexity = calculate_perplexity(mock_model, mock_tokenizer, self.temp_file.name)
        
        # Check that the perplexity is calculated correctly
        self.assertAlmostEqual(perplexity, torch.exp(mock_outputs.loss.item()), places=1)
        
        # Check that the tokenizer was called twice (once for each line)
        self.assertEqual(mock_tokenizer.call_count, 2)
        
        # Check that the model was called twice (once for each line)
        self.assertEqual(mock_model.call_count, 2)


class TestGenerateSampleResponses(unittest.TestCase):
    """Test the generate_sample_responses function"""
    
    def test_generate_sample_responses(self):
        """Test that sample responses are generated correctly"""
        # Create mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Mock the tokenizer.encode to return a tensor
        mock_tokenizer.encode.return_value = torch.tensor([[1, 2, 3]])
        
        # Mock the model.generate to return a tensor
        mock_model.generate.return_value = torch.tensor([[4, 5, 6]])
        
        # Mock the tokenizer.decode to return a string
        mock_tokenizer.decode.return_value = "Generated response"
        
        # Define test prompts
        prompts = ["Prompt 1", "Prompt 2"]
        
        # Call the function
        results = generate_sample_responses(mock_model, mock_tokenizer, prompts)
        
        # Check that the results have the right structure
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["prompt"], "Prompt 1")
        self.assertEqual(results[0]["response"], "Generated response")
        self.assertEqual(results[1]["prompt"], "Prompt 2")
        self.assertEqual(results[1]["response"], "Generated response")
        
        # Check that the tokenizer.encode was called twice (once for each prompt)
        self.assertEqual(mock_tokenizer.encode.call_count, 2)
        
        # Check that the model.generate was called twice (once for each prompt)
        self.assertEqual(mock_model.generate.call_count, 2)
        
        # Check that the tokenizer.decode was called twice (once for each output)
        self.assertEqual(mock_tokenizer.decode.call_count, 2)


class TestMain(unittest.TestCase):
    """Test the main function"""
    
    @patch('evaluate_model.AutoTokenizer.from_pretrained')
    @patch('evaluate_model.AutoModelForCausalLM.from_pretrained')
    @patch('evaluate_model.calculate_perplexity')
    @patch('evaluate_model.generate_sample_responses')
    @patch('json.dump')
    def test_main_pass(self, mock_json_dump, mock_generate, mock_perplexity, 
                      mock_model, mock_tokenizer):
        """Test main function when perplexity is below threshold"""
        # Set up mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_perplexity.return_value = 500.0  # Below threshold of 1000.0
        mock_generate.return_value = [{"prompt": "Test", "response": "Response"}]
        
        # Create a temporary file for validation data
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_file.write("Validation data")
        temp_file.close()
        
        # Create a temporary directory for the model
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary file for output
            output_file = os.path.join(temp_dir, "output.json")
            
            # Call the function
            result = main(temp_dir, temp_file.name, output_file, 1000.0)
            
            # Check that the result is True (passed)
            self.assertTrue(result)
            
            # Check that the model and tokenizer were loaded
            mock_tokenizer.assert_called_once_with(temp_dir)
            mock_model.assert_called_once_with(temp_dir)
            
            # Check that perplexity was calculated
            mock_perplexity.assert_called_once()
            
            # Check that sample responses were generated
            mock_generate.assert_called_once()
            
            # Check that results were saved to file
            mock_json_dump.assert_called_once()
        
        # Clean up
        os.unlink(temp_file.name)
    
    @patch('evaluate_model.AutoTokenizer.from_pretrained')
    @patch('evaluate_model.AutoModelForCausalLM.from_pretrained')
    @patch('evaluate_model.calculate_perplexity')
    @patch('evaluate_model.generate_sample_responses')
    @patch('json.dump')
    def test_main_fail(self, mock_json_dump, mock_generate, mock_perplexity, 
                      mock_model, mock_tokenizer):
        """Test main function when perplexity is above threshold"""
        # Set up mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_perplexity.return_value = 1500.0  # Above threshold of 1000.0
        mock_generate.return_value = [{"prompt": "Test", "response": "Response"}]
        
        # Create a temporary file for validation data
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_file.write("Validation data")
        temp_file.close()
        
        # Create a temporary directory for the model
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary file for output
            output_file = os.path.join(temp_dir, "output.json")
            
            # Call the function
            result = main(temp_dir, temp_file.name, output_file, 1000.0)
            
            # Check that the result is False (failed)
            self.assertFalse(result)
            
            # Check that the model and tokenizer were loaded
            mock_tokenizer.assert_called_once_with(temp_dir)
            mock_model.assert_called_once_with(temp_dir)
            
            # Check that perplexity was calculated
            mock_perplexity.assert_called_once()
            
            # Check that sample responses were generated
            mock_generate.assert_called_once()
            
            # Check that results were saved to file
            mock_json_dump.assert_called_once()
        
        # Clean up
        os.unlink(temp_file.name)


if __name__ == '__main__':
    unittest.main()
