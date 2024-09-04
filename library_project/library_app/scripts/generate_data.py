from pymongo import MongoClient
from neo4j import GraphDatabase
# from cassandra.cluster import Cluster
from settings_cassandra import get_cassandra_session
from faker import Faker
import random
import uuid
import time

# Initialisation de Faker
faker = Faker()

# Connexion à MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['library_db']
books_collection = mongo_db['books']
users_collection = mongo_db['users']

# Connexion à Neo4j
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "fatee26ODC"))

# Connexion à Cassandra
db = get_cassandra_session()
transactions_collection = db.get_collection("transactions")

# Étape 1 : Générer des données de base
genres = ['Fiction', 'Non-Fiction', 'Science Fiction', 'Fantasy', 'Biography', 'Roman', 'Thriller', 'Légende', 'Conte', 'Journal']
authors = [faker.name() for _ in range(10)]

# Générer des utilisateurs (qui incluent les lecteurs et les admins)
def generate_fake_user(user_type):
    return {
        'id': str(uuid.uuid4()),  # Génère un id unique
        'name': faker.name(),
        'email': faker.email(),
        'user_type': user_type,  # 'admin' ou 'reader'
        'password': faker.password(),
        'created_at': faker.date_time_this_year().strftime('%Y-%m-%d %H:%M:%S')
    }

users = [generate_fake_user('reader') for _ in range(25)] + [generate_fake_user('admin') for _ in range(5)]

def generate_fake_book():
    return {
        'id': str(uuid.uuid4()),  # Génère un id unique
        'title': faker.catch_phrase(),
        'summary': faker.text(max_nb_chars=200),
        'author': random.choice(authors),
        'genre': random.choice(genres),
        'published_year': random.randint(1900, 2024)
    }

books = [generate_fake_book() for _ in range(257)]

# Étape 2 : Insertion des livres et utilisateurs dans MongoDB
books_collection.insert_many(books)
users_collection.insert_many(users)

# Étape 3 : Insérer des relations dans Neo4j
def create_book_nodes(tx, book):
    tx.run("""
        MERGE (b:Book {id: $id, title: $title, published_year: $published_year})
        MERGE (a:Author {name: $author})
        MERGE (g:Genre {name: $genre})
        MERGE (a)-[:WROTE]->(b)
        MERGE (b)-[:BELONGS_TO]->(g)
    """, id=book['id'], title=book['title'], author=book['author'], genre=book['genre'], published_year=book['published_year'])
    
    # Ajout de relations de lecture et de recommandation pour les utilisateurs (lecteurs)
    for user in random.sample([u for u in users if u['user_type'] == 'reader'], random.randint(1, 7)):
        tx.run("MERGE (r:Reader {id: $id, name: $name})", id=user['id'], name=user['name'])
        tx.run("""
            MATCH (r:Reader {id: $reader_id}), (b:Book {id: $book_id})
            MERGE (r)-[:READ]->(b)
        """, reader_id=user['id'], book_id=book['id'])
        
        if random.choice([True, False]):
            tx.run("""
                MATCH (r:Reader {id: $reader_id}), (b:Book {id: $book_id})
                MERGE (r)-[:RECOMMENDED]->(b)
            """, reader_id=user['id'], book_id=book['id'])

# Créer des relations pour les utilisateurs dans Neo4j
def create_user_nodes(tx, user):
    tx.run("""
        MERGE (u:User {id: $id, name: $name, email: $email, user_type: $user_type})
    """, id=user['id'], name=user['name'], email=user['email'], user_type=user['user_type'])

with neo4j_driver.session() as session:
    for book in books:
        session.write_transaction(create_book_nodes, book)
    
    for user in users:
        session.write_transaction(create_user_nodes, user)

# Étape 4 : Insérer des logs dans Cassandra
def generate_logs(book):
    for _ in range(random.randint(1, 5)):
        log = {
            "transaction_id": str(uuid.uuid4()),
            "book_id": book['id'],  # Associe l'id du livre à la transaction
            "user_id": random.choice([u['id'] for u in users if u['user_type'] == 'reader']),  # Associe l'id du lecteur à la transaction
            "action": random.choice(['borrowed', 'returned']),
            "timestamp": faker.date_time_this_year().strftime('%Y-%m-%d %H:%M:%S')
        }
        transactions_collection.insert_one(log)

for book in books:
    generate_logs(book)

print("Données insérées avec succès dans MongoDB, Neo4j et Cassandra.")

# Fermer les connexions
mongo_client.close()
neo4j_driver.close()
