"""CLI mínima. Requiere master password (bóveda)."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.vault import Vault, VaultError
from service.cryptoService import CryptoService


def _service():
    vault = Vault()
    if not vault.is_setup:
        print("No vault yet. Run the GUI once to create a master password.")
        sys.exit(1)
    pw = getpass.getpass("Master password: ")
    try:
        vault.unlock(pw)
    except VaultError as e:
        print(e)
        sys.exit(1)
    return CryptoService(vault), vault


def encryptFile(svc):
    file_path = input("File to encrypt: ").strip()
    key = getpass.getpass("Encryption key: ")
    extension, derived_key, bros_path = svc.encryptFile(file_path=file_path, key=key)
    print("Encrypted ->", bros_path)
    if input("Store key in vault? (y/n): ").lower() == "y":
        phrase = svc.generate_mnemonic_passphrase(6)
        h = svc.generate_hash(phrase)
        svc.generate_and_store_key(hash=h, key=derived_key, extension=extension, generated=True)
        print("Passphrase (save it):", phrase)


def decryptFile(svc):
    file_path = input("File to decrypt: ").strip()
    if input("Key from vault? (y/n): ").lower() == "y":
        phrase = input("Passphrase: ").strip()
        item = svc.getItemByHash(svc.generate_hash(phrase))
        if not item:
            print("Not found")
            return
        svc.decryptFile(file_path, item.key, extension=item.extension, generated=True)
    else:
        key = getpass.getpass("Decryption key: ")
        svc.decryptFile(file_path, key, extension=None, generated=False)
    print("Decrypted.")


def mainCli():
    svc, vault = _service()
    try:
        options = {
            "1": ("Encrypt a file", lambda: encryptFile(svc)),
            "2": ("Decrypt a file", lambda: decryptFile(svc)),
            "3": ("View stored keys", lambda: [print(i) for i in svc.getAllItems()]),
            "4": ("Exit", lambda: None),
        }
        while True:
            print("\nSelect an option:")
            for k, (desc, _) in options.items():
                print(f"{k}. {desc}")
            choice = input("Choice: ").strip()
            if choice == "4":
                break
            if choice in options:
                options[choice][1]()
            else:
                print("Invalid")
    finally:
        svc.lock()


if __name__ == "__main__":
    mainCli()
