#!/usr/bin/env python3
"""Setup script to initialize Kanboard with proper project and configuration."""

import json
import requests
import time
import sys


def wait_for_kanboard(url: str, max_attempts: int = 30) -> bool:
    """Wait for Kanboard to be ready."""
    print("Waiting for Kanboard to start...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("Kanboard is ready!")
                return True
        except requests.RequestException:
            pass
        
        print(f"Attempt {attempt + 1}/{max_attempts} - Kanboard not ready yet...")
        time.sleep(2)
    
    return False


def kanboard_api_call(url: str, method: str, params: dict, username: str = "admin", password: str = "admin") -> dict:
    """Make API call to Kanboard."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params
    }
    
    response = requests.post(
        url,
        json=payload,
        auth=(username, password),
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")


def setup_kanboard():
    """Setup Kanboard with proper project and configuration."""
    kanboard_url = "http://localhost:8080"
    api_url = f"{kanboard_url}/jsonrpc.php"
    
    # Wait for Kanboard to be ready
    if not wait_for_kanboard(kanboard_url):
        print("ERROR: Kanboard failed to start within expected time")
        return False
    
    try:
        print("Setting up Kanboard...")
        
        # Check if default project exists
        result = kanboard_api_call(api_url, "getAllProjects", {})
        projects = result.get("result", [])
        
        property_project = None
        for project in projects:
            if project.get("name") == "Property Listings":
                property_project = project
                break
        
        if not property_project:
            print("Creating 'Property Listings' project...")
            result = kanboard_api_call(api_url, "createProject", {
                "name": "Property Listings",
                "description": "Real estate property listings from Funda, Jaap, and Pararius"
            })
            
            if result.get("result"):
                project_id = result["result"]
                print(f"Created project with ID: {project_id}")
                
                # Get project details
                result = kanboard_api_call(api_url, "getProjectById", {"project_id": project_id})
                property_project = result.get("result")
            else:
                print("ERROR: Failed to create project")
                return False
        else:
            print(f"Found existing 'Property Listings' project (ID: {property_project['id']})")
        
        # Create custom columns if they don't exist
        project_id = int(property_project["id"])
        
        # Get existing columns
        result = kanboard_api_call(api_url, "getColumns", {"project_id": project_id})
        columns = result.get("result", [])
        
        desired_columns = ["New Listings", "Under Review", "Interested", "Not Interested"]
        existing_column_names = [col["title"] for col in columns]
        
        # Remove default columns and add our custom ones
        if set(existing_column_names) != set(desired_columns):
            print("Setting up custom columns...")
            
            # Remove existing columns
            for column in columns:
                kanboard_api_call(api_url, "removeColumn", {
                    "project_id": project_id,
                    "column_id": int(column["id"])
                })
            
            # Add our custom columns
            for i, column_name in enumerate(desired_columns):
                kanboard_api_call(api_url, "addColumn", {
                    "project_id": project_id,
                    "title": column_name,
                    "task_limit": 0,
                    "description": f"Column for {column_name.lower()}"
                })
                print(f"Created column: {column_name}")
        
        print("\n" + "="*50)
        print("✅ Kanboard setup completed successfully!")
        print(f"🌐 Access Kanboard at: {kanboard_url}")
        print("👤 Username: admin")
        print("🔑 Password: admin")
        print(f"📋 Project: Property Listings (ID: {property_project['id']})")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to setup Kanboard: {e}")
        return False


if __name__ == "__main__":
    success = setup_kanboard()
    sys.exit(0 if success else 1)