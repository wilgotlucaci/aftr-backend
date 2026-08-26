import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


email = input("Email: ")
password = input("Password: ")

response = supabase.auth.sign_in_with_password(
    {
        "email": email,
        "password": password,
    }
)

print()
print("ACCESS TOKEN:")
print(response.session.access_token)