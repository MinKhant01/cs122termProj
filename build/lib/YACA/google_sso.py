from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from dotenv import load_dotenv
import requests
import webbrowser

load_dotenv()

client_id = os.getenv('GoogleClientID')
client_secret = os.getenv('GoogleClientSecret')

def google_login():
    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.email', 'openid', 'https://www.googleapis.com/auth/userinfo.profile']
    )
    auth_url, _ = flow.authorization_url()
    webbrowser.open(auth_url)
    creds = flow.run_local_server(port=0)
    return creds

def get_user_info(creds):
    userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
    response = requests.get(userinfo_endpoint, headers={"Authorization": f"Bearer {creds.token}"})
    user_info = response.json()
    if user_info.get("email_verified"):
        return {
            'id': user_info["sub"],
            'first_name': user_info["given_name"],
            'last_name': user_info["family_name"],
            'email': user_info["email"],
            'profile_pic': user_info["picture"]
        }
    else:
        raise Exception("User email not available or not verified by Google.")

if __name__ == "__main__":
    creds = google_login()
    user_info = get_user_info(creds)
    print(f"User information:\nName: {user_info['name']}\nEmail: {user_info['email']}\nProfile Pic: {user_info['profile_pic']}")
