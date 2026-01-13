from domain.CryptoBro import CryptoBro
def main():
    crbro = CryptoBro()
    timeNow = crbro.timeNow()

    timeHash = crbro.generateHashByCurrentTime(time = timeNow)
    print("Time-based Hashing: ", timeHash)
    result = crbro.verifyHash(timeNow, timeHash)
    print("Verification: ", result)
    # main.py
    from domain.database import Database

    db = Database('data/tienda.db')
    db.agregar_producto('Laptop', 999.99, 10)

if __name__== "__main__":
    main()