import subprocess
import requests
import json
import time

def get_ngrok_url():
    try:
        # Start ngrok
        ngrok_process = subprocess.Popen(['ngrok', 'http', '80'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for ngrok to initialize
        time.sleep(5)  # Adjust this if needed
        
        # Fetch ngrok's tunnel information from its API
        ngrok_api_response = requests.get('http://localhost:4040/api/tunnels')
        ngrok_data = json.loads(ngrok_api_response.text)
        
        # Extract the public URL
        public_url = ngrok_data['tunnels'][0]['public_url']
        
        # Write the URL to a file
        with open('ngrok_url.txt', 'w') as f:
            f.write(public_url)
        
        print(f'Ngrok URL: {public_url}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    get_ngrok_url()