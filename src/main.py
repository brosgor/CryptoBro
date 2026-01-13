from domain.CryptoBro import CryptoBro
def main():
    crbro = CryptoBro()
    timeNow = crbro.timeNow()

    timeHash = crbro.generateHashByCurrentTime(time = timeNow)
    print("Time-based Hashing: ", timeHash)
    result = crbro.verifyHash(timeNow, timeHash)
    print("Verification: ", result)

if __name__== "__main__":
    main()