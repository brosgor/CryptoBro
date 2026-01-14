from service.cryptoService import CryptoService
def main():
    crbro = CryptoService()
    pathFILE = 'data/incognito.png'
    #key = crbro.generate_key()
    #print(f"Generated Key: {key}")
    paraphrase = "luis123"
    key="luis123"
    print("Encrypting the file...")

    extension = crbro.encryptFile(file_path=pathFILE, key=key)
    print("File encrypted successfully. Quieres guardar la clave? (s/n)")
    choice = input().lower()
    if choice == 's':
        file_hash = crbro.generate_hash(message=paraphrase)
        keyDb = crbro.generate_and_store_key(hash=file_hash,key=key, extension=extension)
        print(f"Key stored with hash: {file_hash} and key: {keyDb}")
    print("Now decrypting the file...")
    extension = crbro.getItemByHash(hash=file_hash)[3]
    crbro.decryptFile(file_path='data/incognito.bros', key=key,extension=extension)
    print("File decrypted successfully.")

if __name__== "__main__":
    main()