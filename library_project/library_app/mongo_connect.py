from pymongo import MongoClient

# Établir la connexion à MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Sélectionner la base de données
db = client['library_db']

# Sélectionner la collection
books_collection = db['books']
