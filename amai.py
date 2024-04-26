from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from rich import print
from openai import OpenAI 
from Crypto.Cipher import AES
import hashlib
import getpass
import os

keyAES = ""
apikey = ""

class endpoint:
    def __init__(self, host, apikey, openai, name):
        self.host = host
        self.apikey = apikey
        self.openai = openai
        self.name = name

def decrypt(ciphertext):
    """Decrypts a ciphertext using AES with the global key"""
    ciphertext = bytes.fromhex(ciphertext)
    iv = ciphertext[: AES.block_size]
    cipher = AES.new(keyAES.encode(), AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext[AES.block_size :]), AES.block_size)
    return decrypted_data.decode()

def encrypt(plaintext):
    """Encrypts text with AES using the global key"""
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(keyAES.encode(), AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    encrypted_data = iv + ciphertext
    return encrypted_data.hex()

def menu(submenu):
    """Displays the menu for the given submenu"""
    print(f"\n [bold cyan]Menu {submenu}[/bold cyan]")
    if submenu == 'account':
        print("1. Delete account")
    elif submenu == 'endpoints':
        print("2. List")
        print("3. Add new")
        print("4. Delete")
    elif submenu == 'chat':
        print("5. Start chat")

    input_menu = input("Choose one: ")

    if input_menu == '1':
        print("Deleting account... \n")
        os.remove("password_hash")
        login()
    elif input_menu == '2':
        print("Listing endpoints... \n")
        listEndpoints()
    elif input_menu == '3':
        print("Adding endpoints... \n")
        addEndpoint()
    elif input_menu == '4':
        print("Removing endpoints... \n")
        removeEndpoint()
    elif input_menu == '5':
        print("Starting chat... \n")
        chat()
    else:
        print("Not valid option! \n")
        exit()

def login():
    """Logs the user in or creates a new account if it doesn't exist"""
    global keyAES
    success = False
    if os.path.exists("password"):
        input_password = getpass.getpass("Enter password: ")
        input_hash = hashlib.sha3_256(input_password.encode()).hexdigest()
        with open("password", "r") as f:
            password = f.read()
        if password == input_hash:
            print("OK !")
            success = True
        else:
            print("Wrong password :(")
            exit()
    else:
        input_password = getpass.getpass("New password: ")
        input_hash = hashlib.sha3_256(input_password.encode()).hexdigest()
        with open("password", "w") as f:
            f.write(input_hash)
        print("Saved!")
        success = True
    if success:
        keyAES = hashlib.sha3_512(input_password.encode()).hexdigest()[:32] #Key used in AES encryption
        menu('endpoints')

def listEndpoints():
    """Lists the endpoints saved in the file and allows the user to choose one"""
    global apikey
    l_hash = []
    l_apikey = []
    l_openai = []
    l_name = []
    try:
        with open("endpoints", "r") as f:
            endpoints = f.readlines()
    except FileNotFoundError:
        print("No endpoints found, adding one...")
        addEndpoint()
    for i, line in enumerate(endpoints):
        host, apikey, openai, name = line.strip().split(",")
        l_hash.append(host)
        l_apikey.append(apikey)
        l_openai.append(openai)
        l_name.append(name)
        print(f"{i} - Name: {name}  Hash: {host[:16]}  OpenAI: {openai}")
    input_choose = input("Choose one: ")
    host = endpoint(l_hash[int(input_choose)], l_apikey[int(input_choose)], l_openai[int(input_choose)], l_name[int(input_choose)])
    chat(host)

def addEndpoint():
    """Adds a new endpoint to the file"""
    input_isopenai = input("\n Is this an OpenAI endpoint? (y/n) ")
    if input_isopenai.upper() == 'Y':
        input_apikey = input("\n OpenAI api key (will be encrypted): ")
        input_name = input("\n Choose a name for this endpoint: ")
        openai = "Y"
        host = "openai"
    else:   
        input_host = input("\n IP or hostname. IE. http://localhost:1234  ")  #TODO check if endpoint is valid
        input_apikey = input("\n Api key (if any): ")
        if(input_apikey == ""):
            input_apikey = "lm-studio" #Default value
        input_name = input("\n Choose a name for this endpoint: ")
        openai = "N"
        host = encrypt(input_host)
    apikey = encrypt(input_apikey)
    with open("endpoints", "a") as f:
        f.write(host + "," + apikey + "," + openai + "," + input_name + "\n")
    print("Saved!")
    menu('endpoints')

def removeEndpoint():
    """Removes an endpoint from the file"""
    with open("endpoints", "r") as f:
        endpoints = f.readlines()
    for i, endpoint in enumerate(endpoints):
        host, apikey, openai, name = endpoint.strip().split(",")
        print(f"{i} - Name: {name}  Hash: {host[:16]}  OpenAI: {openai}")
    input_remove = int(input("Choose one: "))
    del endpoints[input_remove]
    with open("endpoints", "w") as f:
        f.writelines(endpoints)
    print("Removed! \n")
    print("Listing endpoints... \n")
    listEndpoints()

def chat(host):
    """Starts the chat"""
    if(host.openai == 'Y'):
        client = OpenAI(api_key = decrypt(host.apikey)) #TODO: Test OpenAI endpoint
    else:
        client = OpenAI(base_url = decrypt(host.host) + "/v1", api_key = decrypt(host.apikey))
    while True:
        input_message = input("\n Your message: ")
        try:
            completion = client.chat.completions.create(
                model="model",
                messages=[
                    {"role": "system", "content": "You are a helpful, smart, kind, and efficient AI assistant. You always fulfill the user's requests to the best of your ability."},
                    {"role": "user", "content": input_message}
                ],
                temperature=0.7,
            )
            print(f"[bold cyan]{completion.choices[0].message.content}[/bold cyan]")
        except Exception as e:
            print(e)
            exit()

if __name__ == "__main__":
    login()