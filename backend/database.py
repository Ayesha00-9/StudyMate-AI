# Single place where we connect to MongoDB Atlas.
# Every router imports the collections from here.

from pymongo import MongoClient

from config import MONGODB_URI, DATABASE_NAME

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Our four collections.
users_collection = db["users"]
subjects_collection = db["subjects"]
documents_collection = db["documents"]
conversations_collection = db["conversations"]
# Quizzes and exams the student has generated, with their results.
quizzes_collection = db["quizzes"]


def create_indexes():
    """Make sure email is unique. Called once when the server starts."""
    users_collection.create_index("email", unique=True)


def to_str_id(document):
    """MongoDB gives us an ObjectId. JSON cannot handle it, so we turn it into text."""
    if document is None:
        return None
    document = dict(document)
    document["id"] = str(document.pop("_id"))
    return document
