from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_ANON_KEY"]

supabase = create_client(url, key)

email =  "testuser2@demo.com"     #provider3@demo.com #testprovider2@demo.com
password = "User12345678" # (#password for provider 3 : Provider3)  (#password for provider 2 : Provider12345678)

res = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

print("\nACCESS TOKEN:\n")
print(res.session.access_token)