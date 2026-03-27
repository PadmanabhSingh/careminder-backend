from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_ANON_KEY"]

supabase = create_client(url, key)

email =  "testuser1@demo.com" #"testuser2@demo.com"  "provider1@demo.com"  #provider3@demo.com 
password = "12345678" #Provider3 #User12345678

res = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

print("\nACCESS TOKEN:\n")
print(res.session.access_token)