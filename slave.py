import time
import base64

#while True:
print("all your base are belong to us")
# Exemplo de encode/decode base64 duma mensagem de basic authentication
# ID = "root"
# password = "mamacita"
# authHead = ID+":"+password
# authHeadb = authHead.encode("ascii")
# authHeadB64 = base64.b64encode(authHeadb)
# authHead = f"Authentication: Basic {authHeadB64}"
# passDecode = base64.b64decode(authHeadB64)
# passi = passDecode.decode("ascii")
# print(authHead)
# print(passDecode)
# print(passi)

ID = "root"
password = "mamacita"
authHead = ID+":"+password
authHeadb = authHead.encode("ascii")
authHeadB64 = base64.b64encode(authHeadb)
authHead = f"Authentication: Basic {authHeadB64}"



time.sleep(1)
