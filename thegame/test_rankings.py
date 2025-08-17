#!/usr/bin/env python3
"""
Quick test script to debug rankings issues
"""
import requests

def test_rankings():
    """Test rankings endpoint directly"""
    print("Testing rankings...")
    
    # Login first
    session = requests.Session()
    
    login_data = {"username": "testuser", "password": "testpass"}
    login_response = session.post("http://localhost:8083/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    # Select character
    select_response = session.post("http://localhost:8083/character/5/select")
    print(f"Character select status: {select_response.status_code}")
    
    # Test rankings
    rankings_response = session.get("http://localhost:8083/rankings")
    print(f"Rankings status: {rankings_response.status_code}")
    print(f"Rankings content length: {len(rankings_response.text)}")
    
    if rankings_response.status_code != 200:
        print("Rankings error content:")
        print(rankings_response.text[:500])
    else:
        print("Rankings working!")

if __name__ == "__main__":
    test_rankings()