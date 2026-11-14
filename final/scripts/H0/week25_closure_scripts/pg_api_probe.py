import odb
try:
    odb.dbSBox_create()
except TypeError as error:
    print(error)
