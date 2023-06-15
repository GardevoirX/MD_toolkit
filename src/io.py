import pickle

def write_file(data, fileName):
    
    with open(fileName, 'wb') as wfl:
        pickle.dump(data, wfl)
    
    return

def read_file(fileName):
    
    with open(fileName, 'rb') as rfl:
        return pickle.load(rfl)