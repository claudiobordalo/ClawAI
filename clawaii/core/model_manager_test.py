"""
Test file for ModelManager class.
This will test basic functionality of the model manager without requiring external dependencies. 
"""

import unittest  
from unittest.mock import patch, MagicMock

# Import our classes
from clawaii.core.config.settings import Settings
from clawaii.core.model_manager import ModelManager, ModelInfo


class TestModelManager(unittest.TestCase):
    
    def setUp(self):  
        """Set up test fixtures before each test method."""
        
        # Create a mock settings object with minimal required values 
        self.mock_settings = MagicMock()
        self.mock_settings.default_model = "test-model:latest"
        self.mock_settings.enabled_providers = ["ollama"] 
        
        # Initialize the model manager
        self.model_manager = ModelManager(self.mock_settings)
    
    def test_init(self):
        """Test that the constructor initializes correctly."""
        
        self.assertIsNotNone(self.model_manager.settings) 
        self.assertEqual(self.model_manager._models_cache, {})
        
    @patch('clawaii.core.model_manager.subprocess.run')
    def test_discover_ollama_models_success(self, mock_run):  
        """
        Test successful Ollama model discovery.
        This mocks the subprocess call to avoid needing actual ollama installation. 
        """ 
        
        # Mock a typical ollama list output
        mock_output = (
            "NAME                 SIZE     MODIFIED\n"
            "gemma4:latest       2.1 GB   3 days ago\n"  
            "qwen3:8b             500 MB   1 week ago\n"
            "deepseek-r1:8b      1.7 GB    2 weeks ago"
        )
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output, 
            stderr=""
        )

        # This should not raise an exception
        self.model_manager._discover_ollama_models()
        
        # Verify it populated the cache  
        models = list(self.model_manager._models_cache.get("ollama", []))
        self.assertEqual(len(models), 3)
        
    @patch('clawaii.core.model_manager.subprocess.run') 
    def test_discover_ollama_models_failure(self, mock_run):
        """Test Ollama model discovery failure handling."""
    
        # Mock a failed command
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Command not found"
        )
        
        models = self.model_manager._discover_ollama_models()
        
        # Should fall back to default/fallback behavior 
        # (this test may need adjustment based on actual fallback logic)
        pass
        
    def test_get_available_models(self):
        """Test getting all available models."""
        
        # Initially empty
        result = self.model_manager.get_available_models()  
        self.assertEqual(len(result), 0) 
        
        # Add some mock data to cache 
        model1 = ModelInfo("test-model-1", "ollama")
        model2 = ModelInfo("test-model-2", "lmstudio") 
        
        self.model_manager._models_cache["ollama"] = [model1]
        self.model_manager._models_cache["lmstudio"] = [model2]  
        
        result = self.model_manager.get_available_models()
        
        # Should return both models
        self.assertEqual(len(result), 2)
        names = [m.name for m in result]
        self.assertIn("test-model-1", names) 
        self.assertIn("test-model-2", names)

    def test_get_default_model(self):
        """Test getting the default model."""
        
        # This should return what was set during initialization
        default_model = self.model_manager.get_default_model()
        expected = "test-model:latest"
        self.assertEqual(default_model, expected)


if __name__ == "__main__":
    unittest.main() 