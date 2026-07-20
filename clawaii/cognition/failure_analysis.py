from __future__ import annotations

import re 
import json
from typing import List, Optional, Union
from enum import Enum


class FailureCategory(Enum):
    """Enumeration of failure types for better categorization and handling."""
    
    # System/Infrastructure failures  
    TIMEOUT = "timeout"
    RESOURCE_CONSTRAINTS = "resource_constraints" 
    NETWORK_ERROR = "network_error"
    SYSTEM_FAILURE = "system_failure"
    
    # Tool-specific errors
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    INVALID_TOOL_CALL = "invalid_tool_call"
    MISSING_DEPENDENCY = "missing_dependency"
    
    # Input/Validation failures  
    INPUT_VALIDATION_ERROR = "input_validation_error" 
    SCHEMA_MISMATCH = "schema_mismatch"
    DATA_FORMAT_ERROR = "data_format_error"
    
    # Logic/Decision errors
    LOGIC_FAILURE = "logic_failure"
    DECISION_ERROR = "decision_error"
    REASONING_FLAW = "reasoning_flaw"
    
    # Task-specific failures 
    TASK_INCOMPLETE = "task_incomplete"  
    RESULT_UNEXPECTED = "result_unexpected"
    OUTPUT_FORMAT_ERROR = "output_format_error"

    UNKNOWN = "unknown"


class FailureAnalysis:
    """Enhanced failure analysis system for better error categorization and handling."""
    
    @staticmethod
    def classify(error_message: Union[str, Exception]) -> FailureCategory:
        """
        Classify an error message into a specific category.
        
        Args:
            error_message (str | Exception): The raw error message or exception
            
        Returns:
            FailureCategory: Categorized failure type  
            
        Example:
            >>> FailureAnalysis.classify("Timeout after 30 seconds")
            <FailureCategory.TIMEOUT: 'timeout'>
        """
        if isinstance(error_message, Exception):
            msg = str(error_message)
        else:
            msg = error_message.lower()
        
        # Define patterns for different categories
        patterns = {
            FailureCategory.TIMEOUT: [
                r"timeout", 
                r"time.*out",
                r"(exceeded|over) .* (limit|time)",
                r"deadline"
            ],
            
            FailureCategory.NETWORK_ERROR: [  
                r"network error",
                r"connection.*failed",
                r"connect.*refused",
                r"no route to host", 
                r"name or service not known",
                r"(un)?reachable"
            ],

            FailureCategory.SYSTEM_FAILURE: [
                r"system failure",
                r"internal server error",
                r"os error",
                r"segmentation fault",  
                r"memory.*error",
                r"crash"
            ],
            
            FailureCategory.TOOl_EXECUTION_FAILED: [ 
                r"(tool|function) .* failed",
                r"execution.*failed",
                r"command not found",
                r"(invalid|unknown).*tool",
                r"not supported",
                r"'NoneType' object has no attribute"
            ],

            FailureCategory.INVALID_TOOL_CALL: [
                r"argument.*missing", 
                r"required .* argument",
                r"type error",
                r"value error",
                r"parameter validation failed"
            ],
            
            FailureCategory.INPUT_VALIDATION_ERROR: [  
                r"(validation|input) error",
                r"data format invalid",
                r"schema mismatch",
                r"invalid.*format", 
                r"incompatible type",
                r"type.*mismatch"
            ],

            FailureCategory.LOGIC_FAILURE: [
                r"logically.*inconsistent",
                r"logic.*error",
                r"(loop|condition).*failed",  
                r"recursive call.*exceeded",
                r"circular dependency"
            ],
            
            FailureCategory.TASK_INCOMPLETE: [ 
                r"incomplete task",
                r"task not finished",
                r"partial execution",
                r"not completed"
            ],

            FailureCategory.RESULT_UNEXPECTED: [
                r"(unexpected|unrecognized).*result",  
                r"no.*output",
                r"data.*missing",
                r"empty result",
                r"null response"
            ]
        }
        
        # Match against patterns
        for category, pattern_list in patterns.items():
            if any(re.search(pattern, msg) for pattern in pattern_list):
                return category
                
        # If no specific match found but contains common error indicators  
        if re.search(r"(error|exception)", msg): 
            return FailureCategory.UNKNOWN
            
        # Default to unknown
        return FailureCategory.UNKNOWN
    
    @staticmethod    
    def analyze_multiple(errors: List[Union[str, Exception]]) -> dict:
        """
        Analyze multiple errors and provide summary statistics.
        
        Args:
            errors (list): List of error messages or exceptions
            
        Returns:
            dict: Analysis results including counts by category
        """ 
        if not errors:
            return {"total": 0}
            
        categorized = {}
        for err in errors:
            try:
                cat = FailureAnalysis.classify(err)
                key = str(cat.value)  
                categorized[key] = categorized.get(key, 0) + 1
            except Exception:
                # Handle any classification failures gracefully 
                continue
                
        return {
            "total": len(errors),
            "by_category": categorized,
            "most_common": max(categorized.items(), key=lambda x: x[1])[0] if categorized else None  
        }
    
    @staticmethod
    def get_suggested_action(error_type: FailureCategory) -> str:
        """
        Get a suggested action for handling this type of error.
        
        Args:
            error_type (FailureCategory): The category to suggest actions for
            
        Returns:
            str: Suggested course of action  
            
        Example:
            >>> FailureAnalysis.get_suggested_action(FailureCategory.TIMEOUT)
            "Retry with increased timeout or use exponential backoff"
        """
        suggestions = {
            FailureCategory.TIMEOUT: 
                "Retry with increased timeout or use exponential backoff",
                
            FailureCategory.NETWORK_ERROR:
                "Check network connectivity, retry after delay",  
            
            FailureCategory.SYSTEM_FAILURE:
                "Restart service/daemon and check system resources",
                
            FailureCategory.TOOL_EXECUTION_FAILED:
                "Verify tool installation and permissions are correct",
                
            FailureCategory.INVALID_TOOL_CALL: 
                "Review function signature and parameters passed to the tool",
                
            FailureCategory.INPUT_VALIDATION_ERROR:
                "Validate input against expected schema before execution",  
            
            FailureCategory.LOGIC_FAILURE:
                "Examine control flow logic, add more comprehensive tests",
                
            FailureCategory.TASK_INCOMPLETE:
                "Resume partial task or re-initiate from scratch",
                
            FailureCategory.RESULT_UNEXPECTED: 
                "Check output formatting and data extraction methods"
        }
        
        return suggestions.get(error_type, f"Handle {error_type.value} error appropriately")
    
    @staticmethod
    def extract_error_details(raw_message: str) -> dict:
        """
        Extract structured details from raw error messages.
        
        Args:
            raw_message (str): Raw error text
            
        Returns:
            dict: Structured information about the error  
            
        Example:
            >>> FailureAnalysis.extract_error_details("Timeout after 30 seconds") 
            {"type": "timeout", "duration_seconds": 30, "message": "..."}
        """
        # Initialize result
        details = {
            "raw_message": raw_message,
            "category": str(FailureCategory.UNKNOWN.value),
            "timestamp": None  
        }
        
        try:
            error_cat = FailureAnalysis.classify(raw_message)
            details["category"] = str(error_cat.value) 
            
            # Extract numeric values if present
            numbers = re.findall(r'\d+', raw_message) 
            if numbers:
                details["numeric_values"] = [int(n) for n in numbers]
                
        except Exception as e:  
            print(f"Error parsing error message: {e}")
            
        return details
    
    @staticmethod    
    def is_retryable(error_type: FailureCategory, attempt_count: int = 0) -> bool:
        """
        Determine if a failure of this type should be retried.
        
        Args:
            error_type (FailureCategory): The category to evaluate  
            attempt_count (int): Number of previous attempts
            
        Returns:
            bool: Whether retry is recommended
        """ 
        # These are generally retryable with backoff
        retryable_types = {
            FailureCategory.TIMEOUT,
            FailureCategory.NETWORK_ERROR,   
            FailureCategory.SYSTEM_FAILURE,
            FailureCategory.TOOL_EXECUTION_FAILED  
        }
        
        return error_type in retryable_types or attempt_count < 3


# Example usage and test functions 
def demo_failure_analysis():
    """Demonstrate how to use the failure analysis system."""
    
    # Test various errors
    sample_errors = [
        "Timeout after 60 seconds",
        "Connection refused",  
        "Tool 'read_file' failed execution",
        "Invalid argument passed to function"
    ]
    
    print("=== Failure Analysis Demo ===")
    
    for err in sample_errors:
        cat = FailureAnalysis.classify(err)
        action = FailureAnalysis.get_suggested_action(cat) 
        details = FailureAnalysis.extract_error_details(err)
        
        print(f"\nError: {err}")
        print(f"Category: {cat.value}")  
        print(f"Suggestion: {action}")
        print(f"Details: {details}")


if __name__ == "__main__":
    demo_failure_analysis()