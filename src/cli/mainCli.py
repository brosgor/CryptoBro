"""CLI mínima. Requiere clave maestra (bóveda)."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.vault import Vault, VaultError
from service.cryptoService import CryptoService


def _service():
    vault = Vault()
    if not vault.is_setup:
        print("Aún no hay bóveda. Abre la interfaz una vez para crear la clave maestra.")
        sys.exit(1)
    pw = getpass.getpass("Clave maestra: ")
    try:
        vault.unlock(pw)
    except VaultError as e:
        print(e)
        sys.exit(1)
    return CryptoService(vault), vault


def encryptFile(svc):
    file_path = input("Archivo a cifrar: ").strip()
    key = getpass.getpass("Clave de cifrado: ")
    extension, derived_key, bros_path = svc.encryptFile(file_path=file_path, key=key)
    print("Cifrado ->", bros_path)
    if input("¿Guardar clave en la bóveda? (s/n): ").lower() == "s":
        phrase = svc.generate_mnemonic_passphrase(6)
        h = svc.generate_hash(phrase)
        svc.generate_and_store_key(hash=h, key=derived_key, extension=extension, generated=True)
        print("Frase (guárdala):", phrase)


def decryptFile(svc):
    file_path = input("Archivo a descifrar: ").strip()
    if input("¿Clave desde la bóveda? (s/n): ").lower() == "s":
        phrase = input("Frase de recuperación: ").strip()
        item = svc.getItemByHash(svc.generate_hash(phrase))
        if not item:
            print("No encontrada")
            return
        svc.decryptFile(file_path, item.key, extension=item.extension, generated=True)
    else:
        key = getpass.getpass("Clave de descifrado: ")
        svc.decryptFile(file_path, key, extension=None, generated=False)
    print("Descifrado.")


def mainCli():
    svc, vault = _service()
    try:
        options = {
            "1": ("Cifrar un archivo", lambda: encryptFile(svc)),
            "2": ("Descifrar un archivo", lambda: decryptFile(svc)),
            "3": ("Ver claves guardadas", lambda: [print(i) for i in svc.getAllItems()]),
            "4": ("Salir", lambda: None),
        }
        while True:
            print("\nElige una opción:")
            for k, (desc, _) in options.items():
                print(f"{k}. {desc}")
            choice = input("Opción: ").strip()
            if choice == "4":
                break
            if choice in options:
                options[choice][1]()
            else:
                print("Opción no válida")
    finally:
        svc.lock()


if __name__ == "__main__":
    mainCli()
