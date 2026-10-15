import json
import sys
import os

# Add current directory to path so we can import server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from server import app, search_products
    print("✅ Successfully imported server.py")
except ImportError as e:
    print(f"❌ Failed to import server.py: {e}")
    sys.exit(1)

def test_search_logic(query):
    print(f"Testing logic for: '{query}'")
    with app.test_request_context(f'/api/search?q={query}'):
        try:
            response = search_products()
            # response is a Flask Response object, need to get json
            results = response.get_json()
            
            print(f"Found {len(results)} results")
            if results:
                first = results[0]
                print(f"First result: {first.get('productDisplayName')}")
                print(f"Image URL: {first.get('image')}")
                
                # Check if image path is correct format
                if first.get('image', '').startswith('/fashion-dataset/images/'):
                    print("✅ Image path format is correct")
                else:
                    print(f"❌ Image path format is incorrect: {first.get('image')}")
            else:
                print("⚠️ No results found")
        except Exception as e:
            print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    test_search_logic("mens tshirt")
    print("-" * 20)
    test_search_logic("women bag")

