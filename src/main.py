from domain.cryptoBro import CryptoBro
def main():
    crbro = CryptoBro()
    timeNow = crbro.timeNow()

    timeHash = crbro.generateHashByCurrentTime(time = timeNow)
    print("Time-based Hashing: ", timeHash)
    result = crbro.verifyHash(timeNow, timeHash)
    print("Verification: ", result)
    # main.py
    from repository.database import Database

    db = Database('data/secure.db')
    db.addItem(hash=timeHash, key=crbro.generateKey(), extension=".mp2")

    item = db.getItemByHash(timeHash)
    print("Retrieved Item: ", item)
if __name__== "__main__":
    main()