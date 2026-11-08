"""
Mentori MCP Tool Blueprint
==========================

This file serves as a template and guide for creating new tools for the Mentori platform.
To create a new toolset, copy this structure into a new file in `backend/mcp/custom/`.

Key Concepts:
1.  **Decorator**: Use `@mentori_tool` to register the function.
2.  **Type Hints**: REQUIRED. Used to generate the JSON Schema for the LLM.
3.  **Docstrings**: REQUIRED. Used as the tool's description/prompt for the LLM.
4.  **Secrets**: Declare required API keys in `secrets=["KEY_NAME"]`.

"""

from typing import List, Optional
from backend.mcp.decorator import mentori_tool

# --- Example 1: A Simple Calculation Tool ---

@mentori_tool(category="math")
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """
    Calculates Body Mass Index (BMI).
    
    Args:
        weight_kg: Weight in kilograms (e.g., 70.5)
        height_m: Height in meters (e.g., 1.75)
        
    Returns:
        A string with the BMI and category.
    """
    if height_m <= 0:
        return "Error: Height must be positive."
        
    bmi = weight_kg / (height_m ** 2)
    
    category = "Normal"
    if bmi < 18.5: category = "Underweight"
    elif bmi >= 25: category = "Overweight"
    
    return f"BMI: {bmi:.1f} ({category})"


# --- Example 2: External API Tool (With Secrets) ---

@mentori_tool(
    category="weather",
    secrets=["WEATHER_API_KEY"] # The system will auto-inject this from User Settings
)
def get_current_weather(city: str, country: str = "US", WEATHER_API_KEY: str = None) -> str:
    """
    Fetches current weather for a city.
    
    Args:
        city: Name of the city
        country: Two-letter country code (default: US)
    """
    if not WEATHER_API_KEY:
        return "Error: WEATHER_API_KEY not configured in User Settings."
        
    # simulate_api_call(city, key=WEATHER_API_KEY)
    return f"Weather in {city}, {country}: Sunny, 25°C (Simulated)"


# --- Example 3: Context Aware Tool (Session Context Injection) ---
# NOTE: user_id, task_id, and workspace_path are SESSION CONTEXT values,
# NOT secrets/API keys. They are auto-injected by name matching, WITHOUT
# needing to be listed in secrets=[]. Just declare them as parameters.

@mentori_tool(
    category="system"
    # No secrets needed - user_id is auto-injected from session context
)
def get_my_data(data_type: str, user_id: str) -> str:
    """
    Retrieves private user data. The user_id is auto-injected and hidden from the Agent/LLM.

    Args:
        data_type: Type of data to retrieve
        user_id: [Auto-injected] The authenticated user's UUID
    """
    return f"Retrieving {data_type} for User UUID: {user_id}"
