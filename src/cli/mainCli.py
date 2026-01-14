from service.cryptoService import CryptoService
crbro = CryptoService()
def encryptFile():
    file_path = input("Enter the file path to encrypt: ")
    key = input("Enter the encryption key: ")
    pharase = input("Enter a passphrase (optional): ")
    extension, derived_key = crbro.encryptFile(file_path=file_path, key=key)
    print(f"File encrypted successfully with extension: {extension}")
    if input("Do you want to store the key? (y/n): ").lower() == 'y':
        hash = crbro.generate_hash(message=pharase)
        crbro.generate_and_store_key(hash=hash, key=derived_key, extension=extension, generated=True)
        print(f"Key stored with hash: {hash}")
    else:
        print("Key not stored.")
def decryptFile():
        file_path = input("Enter the file path to decrypt: ")
        askForDb = input("Do you want to retrieve the key from the database? (y/n): ").lower()
        paraphrase = input("Enter the hash to retrieve the extension: ")
        hash = crbro.generate_hash(message=paraphrase)

        if askForDb == 'y':
            item = crbro.getItemByHash(hash=hash)
            if item:
                extension = item.extension
                key = item.key
            else:
                print("No item found with the provided hash.")
                return
        elif askForDb == 'n':
            key = input("Enter the decryption key: ")
            extension = None
        crbro.decryptFile(file_path=file_path, key=key, extension=extension,generated=True if askForDb == 'y' else False)
        print("File decrypted successfully.")
def getAllItems():
    items = crbro.getAllItems()
    for item in items:
        print(item)

def mainCli():
    options = {
        '1': ('Encrypt a file', encryptFile),
        '2': ('Decrypt a file', decryptFile),
        '3': ('View all stored keys', getAllItems),
        '4': ('Exit', exit)
    }
    while True:
        print("\nSelect an option:")
        for key, (desc, _) in options.items():
            print(f"{key}. {desc}")
        choice = input("Enter your choice: ")
        if choice in options:
            options[choice][1]()
        else:
            print("Invalid choice. Please try again.")
    
