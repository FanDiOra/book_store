from django.http import JsonResponse
from neo4j import GraphDatabase
from django.views.decorators.csrf import csrf_exempt
from .mongo_connect import books_collection
from library_app.scripts.settings_cassandra import get_cassandra_session
import json
import uuid
import time
import redis

# Connexion à Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Connexion à Neo4j
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "fatee26ODC"))

# Connexion à Cassandra
db = get_cassandra_session()
transactions_collection = db.get_collection("transactions")

# Create your views here.

# -------------------- TEST -------------------

@csrf_exempt
def simple_view(request):
    if request.method == "POST":
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# -------------------- ADMIN -------------------

@csrf_exempt
def add_book(request):
    if request.method == "POST":
        data = json.loads(request.body)
        new_book = {
            'id': str(uuid.uuid4()),  # Génère un id unique pour le livre
            'title': data.get('title'),
            'summary': data.get('summary'),
            'author': data.get('author'),
            'genre': data.get('genre'),
            'published_year': int(data.get('published_year')),
        }
        result = books_collection.insert_one(new_book)
        return JsonResponse({'status': 'success', 'book_id': str(result.inserted_id)})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def edit_book(request, book_id):
    if request.method in ["PUT", "PATCH"]:
        data = json.loads(request.body)
        updated_book = {
            'title': data.get('title'),
            'summary': data.get('summary'),
            'author': data.get('author'),
            'genre': data.get('genre'),
            'published_year': int(data.get('published_year')),
        }
        result = books_collection.update_one({'id': book_id}, {"$set": updated_book})
        if result.modified_count:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'No update performed'}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def delete_book(request, book_id):
    if request.method == "DELETE":
        result = books_collection.delete_one({'id': book_id})
        if result.deleted_count:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Book not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)


# -------------------- USER -------------------

def get_books_by_genre(request, genre):
    books_cursor = books_collection.find({'genre': genre})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'summary': book.get('summary', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    return JsonResponse({'books': books_list})


# -------------------- ADMIN/USER -------------------

def get_books(request):
    books_cursor = books_collection.find({})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'summary': book.get('summary', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    return JsonResponse({'books': books_list})

def get_book(request, book_id):
    book = books_collection.find_one({'id': book_id})
    if book:
        return JsonResponse({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'summary': book.get('summary', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    return JsonResponse({'status': 'error', 'message': 'Book not found'}, status=404)

def get_books_by_author(request, author):
    books_cursor = books_collection.find({'author': author})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'summary': book.get('summary', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    return JsonResponse({'books': books_list})

def get_books_by_reader(request, reader_id):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (r:Reader {id: $reader_id})-[:READ]->(b:Book)
            RETURN b.title AS title, b.id AS id, COUNT(*) AS read_count
            ORDER BY read_count DESC
        """, reader_id=reader_id)
        
        books_list = []
        for record in result:
            books_list.append({
                'id': record['id'],
                'title': record['title'],
                'read_count': record['read_count']
            })
        
        return JsonResponse({'books': books_list})


# -------------------- TRANSACTIONS -------------------

@csrf_exempt
def borrow_book(request):
    if request.method == "POST":
        data = json.loads(request.body)
        transaction_id = str(uuid.uuid4())
        book_id = data.get('book_id')
        user_id = data.get('user_id')
        action = 'borrowed'
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        # Insertion dans AstraDB
        transactions_collection.insert_one({
            "transaction_id": transaction_id,
            "book_id": book_id,
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp
        })
        
        return JsonResponse({'status': 'success', 'transaction_id': transaction_id})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def return_book(request):
    if request.method == "POST":
        data = json.loads(request.body)
        transaction_id = str(uuid.uuid4())
        book_id = data.get('book_id')
        user_id = data.get('user_id')
        action = 'returned'
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        # Insertion dans AstraDB
        transactions_collection.insert_one({
            "transaction_id": transaction_id,
            "book_id": book_id,
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp
        })
        
        return JsonResponse({'status': 'success', 'transaction_id': transaction_id})
    return JsonResponse({'status': 'error'}, status=400)

def get_transaction(request, transaction_id):
    transaction = transactions_collection.find_one({'transaction_id': transaction_id})
    
    if transaction:
        return JsonResponse({
            'transaction_id': transaction.get('transaction_id'),
            'book_id': transaction.get('book_id'),
            'user_id': transaction.get('user_id'),
            'action': transaction.get('action'),
            'timestamp': transaction.get('timestamp')
        })
    return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

def get_all_transactions(request):
    transactions_cursor = transactions_collection.find({})
    
    transactions_list = []
    for transaction in transactions_cursor:
        transactions_list.append({
            'transaction_id': transaction.get('transaction_id'),
            'book_id': transaction.get('book_id'),
            'user_id': transaction.get('user_id'),
            'action': transaction.get('action'),
            'timestamp': transaction.get('timestamp')
        })
    
    return JsonResponse({'transactions': transactions_list})

def get_transactions_by_user(request, user_id):
    # Recherche des transactions de l'utilisateur spécifique
    transactions_cursor = transactions_collection.find({'user_id': user_id})
    
    transactions_list = []
    for transaction in transactions_cursor:
        transactions_list.append({
            'transaction_id': transaction.get('transaction_id'),
            'book_id': transaction.get('book_id'),
            'user_id': transaction.get('user_id'),
            'action': transaction.get('action'),
            'timestamp': transaction.get('timestamp')
        })
    
    return JsonResponse({'transactions': transactions_list})

@csrf_exempt
def edit_transaction(request, transaction_id):
    if request.method in ["PUT", "PATCH"]:
        data = json.loads(request.body)
        
        updated_transaction = {
            'book_id': data.get('book_id'),
            'user_id': data.get('user_id'),
            'action': data.get('action'),
            'timestamp': data.get('timestamp')
        }
        
        result = transactions_collection.update_one({'transaction_id': transaction_id}, {"$set": updated_transaction})
        
        # if result.modified_count:
        #     return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'success', 'transaction_id': transaction_id})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def delete_transaction(request, transaction_id):
    if request.method == "DELETE":
        result = transactions_collection.delete_one({'transaction_id': transaction_id})
        
        if result.deleted_count:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

# -------------------- RECOMMENDATIONS / RELATIONS -------------------

@csrf_exempt
def recommend_book(request, user_id):
    if request.method == "POST":
        data = json.loads(request.body)
        book_id = data.get('book_id')
        
        with neo4j_driver.session() as session:
            session.run("""
                MATCH (u:User {id: $user_id}), (b:Book {id: $book_id})
                MERGE (u)-[:RECOMMENDED]->(b)
            """, user_id=user_id, book_id=book_id)
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def get_user_recommendations(request, user_id):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (u:User {id: $user_id})-[:RECOMMENDED]->(b:Book)
            RETURN b.id AS book_id, b.title AS title
        """, user_id=user_id)
        
        recommendations = []
        for record in result:
            recommendations.append({
                'book_id': record['book_id'],
                'title': record['title']
            })
        
        return JsonResponse({'recommendations': recommendations})

def get_books_by_recommendations(request):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (:User)-[r:RECOMMENDED]->(b:Book)
            RETURN b.id AS book_id, b.title AS title, COUNT(r) AS recommendations_count
            ORDER BY recommendations_count DESC
        """)
        
        books_list = []
        for record in result:
            books_list.append({
                'book_id': record['book_id'],
                'title': record['title'],
                'recommendations_count': record['recommendations_count']
            })
        
        return JsonResponse({'books': books_list})

def get_book_relationships(request, book_id):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (b:Book {id: $book_id})<-[:WROTE]-(a:Author)
            MATCH (r:Reader)-[:READ]->(b)
            RETURN a.name AS author_name, r.name AS reader_name
        """, book_id=book_id)
        
        relationships = {
            'author': None,
            'readers': []
        }
        
        for record in result:
            if not relationships['author']:
                relationships['author'] = record['author_name']
            relationships['readers'].append(record['reader_name'])
        
        return JsonResponse({'relationships': relationships})


# -------------------- CACHE -------------------

def get_books_by_title_cached(request, title):
    cache_key = f'books_by_title:{title}'
    cached_books = redis_client.get(cache_key)
    
    if cached_books:
        # Si les résultats sont en cache, les retourner
        return JsonResponse({'books': json.loads(cached_books)})
    
    # Sinon, effectuer la recherche dans la base de données
    books_cursor = books_collection.find({'title': {'$regex': title, '$options': 'i'}})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    
    # Mettre les résultats en cache pour une durée de 10 minutes (600 secondes)
    redis_client.setex(cache_key, 600, json.dumps(books_list))
    
    return JsonResponse({'books': books_list})

def get_books_by_author_cached(request, author):
    cache_key = f'books_by_author:{author}'
    cached_books = redis_client.get(cache_key)
    
    if cached_books:
        # Si les résultats sont en cache, les retourner
        return JsonResponse({'books': json.loads(cached_books)})
    
    # Sinon, effectuer la recherche dans la base de données
    books_cursor = books_collection.find({'author': {'$regex': author, '$options': 'i'}})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    
    # Mettre les résultats en cache pour 10 minutes
    redis_client.setex(cache_key, 600, json.dumps(books_list))
    
    return JsonResponse({'books': books_list})

def get_books_by_genre_cached(request, genre):
    cache_key = f'books_by_genre:{genre}'
    cached_books = redis_client.get(cache_key)
    
    if cached_books:
        # Si les résultats sont en cache, les retourner
        return JsonResponse({'books': json.loads(cached_books)})
    
    # Sinon, effectuer la recherche dans la base de données
    books_cursor = books_collection.find({'genre': genre})
    books_list = []
    for book in books_cursor:
        books_list.append({
            'id': str(book['id']),
            'title': book.get('title', 'N/A'),
            'author': book.get('author', 'N/A'),
            'genre': book.get('genre', 'N/A'),
            'published_year': book.get('published_year', 'N/A')
        })
    
    # Mettre les résultats en cache pour 10 minutes
    redis_client.setex(cache_key, 600, json.dumps(books_list))
    
    return JsonResponse({'books': books_list})
