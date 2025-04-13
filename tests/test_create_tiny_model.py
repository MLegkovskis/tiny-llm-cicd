"""
Unit tests for create_tiny_model.py
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import torch
from torch.optim import AdamW
from transformers import AutoTokenizer

# Import the module to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from create_tiny_model import TextDataset, fine_tune_model, main


class TestTextDataset(unittest.TestCase):
    """Test the TextDataset class"""

    def setUp(self):
        # Create a temporary file with test data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.temp_file.write("This is a test sentence.\nThis is another test sentence.")
        self.temp_file.close()
        
        # Create a tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
        
    def tearDown(self):
        # Remove the temporary file
        os.unlink(self.temp_file.name)
        
    def test_dataset_initialization(self):
        """Test that the dataset is initialized correctly"""
        dataset = TextDataset(self.tokenizer, self.temp_file.name)
        
        # Check that the dataset has the correct number of examples
        self.assertEqual(len(dataset), 2)
        
        # Check that the examples are tensors
        self.assertIsInstance(dataset[0], torch.Tensor)
        
        # Check that the tensors have the correct data type
        self.assertEqual(dataset[0].dtype, torch.long)


class TestFineTuneModel(unittest.TestCase):
    """Test the fine_tune_model function"""
    
    @patch('create_tiny_model.DataLoader')
    @patch('torch.optim.AdamW')
    @patch('create_tiny_model.get_linear_schedule_with_warmup')
    def test_fine_tune_model_calls(self, mock_scheduler, mock_optimizer, mock_dataloader):
        """Test that fine_tune_model calls the right functions"""
        # Create mocks
        mock_model = MagicMock()
        # Mock model.parameters() to return a non-empty list
        mock_params = [torch.nn.Parameter(torch.randn(2, 2))]
        mock_model.parameters.return_value = mock_params
        
        mock_tokenizer = MagicMock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "[EOS]"
        
        # Create a temporary file with test data
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_file.write("This is a test sentence.\nThis is another test sentence.")
        temp_file.close()
        
        # Mock the DataLoader to return a list of batches
        mock_batch = torch.tensor([[1, 2, 3], [4, 5, 6]])
        mock_dataloader.return_value = [mock_batch]
        
        # Mock the optimizer
        mock_optimizer_instance = MagicMock()
        mock_optimizer.return_value = mock_optimizer_instance
        
        # Mock the scheduler
        mock_scheduler_instance = MagicMock()
        mock_scheduler.return_value = mock_scheduler_instance
        
        # Mock the model's forward pass
        mock_outputs = MagicMock()
        mock_outputs.loss = torch.tensor(0.5)
        mock_model.return_value = mock_outputs
        
        # Call the function
        fine_tune_model(mock_model, mock_tokenizer, temp_file.name, epochs=1, batch_size=2)
        
        # Check that the tokenizer's pad_token was set
        self.assertEqual(mock_tokenizer.pad_token, mock_tokenizer.eos_token)
        
        # Check that the optimizer was called with the model's parameters
        mock_optimizer.assert_called_once_with(mock_params, lr=1e-5)
        
        # Check that the scheduler was called
        mock_scheduler.assert_called_once()
        
        # Check that the model was called with the right arguments
        mock_model.assert_called_once()
        
        # Check that optimizer step was called
        mock_optimizer_instance.step.assert_called()
        
        # Check that scheduler step was called
        mock_scheduler_instance.step.assert_called()
        
        # Clean up
        os.unlink(temp_file.name)


class TestMain(unittest.TestCase):
    """Test the main function"""
    
    @patch('create_tiny_model.download_model_from_gcs')
    @patch('create_tiny_model.AutoTokenizer.from_pretrained')
    @patch('create_tiny_model.AutoModelForCausalLM.from_pretrained')
    @patch('create_tiny_model.fine_tune_model')
    @patch('create_tiny_model.upload_model_to_gcs')
    def test_main_with_gcs_success(self, mock_upload, mock_fine_tune, mock_model, 
                                  mock_tokenizer, mock_download):
        """Test main function when GCS download succeeds"""
        # Set up mocks
        mock_download.return_value = True
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Call the function
            main(train=False, force_train=False, gcs_path="gs://bucket/path", 
                 data_file="data.txt", model_dir=temp_dir)
            
            # Check that download was called
            mock_download.assert_called_once_with("gs://bucket/path", temp_dir)
            
            # Check that the model and tokenizer were not loaded
            mock_tokenizer.assert_not_called()
            mock_model.assert_not_called()
            
            # Check that fine_tune was not called
            mock_fine_tune.assert_not_called()
            
            # Check that upload was not called
            mock_upload.assert_not_called()
    
    @patch('create_tiny_model.download_model_from_gcs')
    @patch('create_tiny_model.AutoTokenizer.from_pretrained')
    @patch('create_tiny_model.AutoModelForCausalLM.from_pretrained')
    @patch('create_tiny_model.fine_tune_model')
    @patch('create_tiny_model.upload_model_to_gcs')
    def test_main_with_gcs_failure_and_train(self, mock_upload, mock_fine_tune, 
                                           mock_model, mock_tokenizer, mock_download):
        """Test main function when GCS download fails and training is enabled"""
        # Set up mocks
        mock_download.return_value = False
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Call the function
            main(train=True, force_train=False, gcs_path="gs://bucket/path", 
                 data_file="data.txt", model_dir=temp_dir)
            
            # Check that download was called
            mock_download.assert_called_once_with("gs://bucket/path", temp_dir)
            
            # Check that the model and tokenizer were loaded
            mock_tokenizer.assert_called_once_with("distilgpt2")
            mock_model.assert_called_once_with("distilgpt2")
            
            # Check that fine_tune was called
            mock_fine_tune.assert_called_once()
            
            # Check that upload was called
            mock_upload.assert_called_once_with(temp_dir, "gs://bucket/path")


if __name__ == '__main__':
    unittest.main()
