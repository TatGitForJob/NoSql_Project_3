import argparse
import random
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError

from config import COLLECTION_NAME, DB_NAME, MONGO_URI


def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


def ensure_indexes(collection):
    collection.create_index([("student_id", ASCENDING)], unique=True)


def serialize_student(doc: dict[str, Any]) -> dict[str, Any]:
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


def add_student(args):
    collection = get_collection()
    ensure_indexes(collection)
    student = {
        "student_id": args.student_id,
        "full_name": args.full_name,
        "group": args.group,
        "faculty": args.faculty,
        "admission_year": args.admission_year,
    }
    try:
        collection.insert_one(student)
    except DuplicateKeyError:
        raise SystemExit(f"student_id '{args.student_id}' already exists")
    print("added", student["student_id"])


def get_student(args):
    collection = get_collection()
    doc = collection.find_one({"student_id": args.student_id})
    if not doc:
        raise SystemExit(f"student_id '{args.student_id}' not found")
    print(serialize_student(doc))


def list_students(args):
    collection = get_collection()
    cursor = collection.find({}, {"_id": 0}).sort("student_id", ASCENDING).limit(args.limit)
    for doc in cursor:
        print(doc)


def build_student(index: int) -> dict[str, Any]:
    faculties = ["Engineering", "Economics", "Law", "Physics"]
    groups = ["A-101", "B-202", "C-303", "D-404"]
    years = [2021, 2022, 2023, 2024]
    return {
        "student_id": f"S{index:06d}",
        "full_name": f"Student {index}",
        "group": random.choice(groups),
        "faculty": random.choice(faculties),
        "admission_year": random.choice(years),
    }


def seed_students(args):
    collection = get_collection()
    ensure_indexes(collection)
    documents = [build_student(index) for index in range(args.count)]
    if not documents:
        print("no documents to insert")
        return
    collection.insert_many(documents, ordered=False)
    print("seeded", len(documents))


def build_parser():
    parser = argparse.ArgumentParser(description="Minimal CLI for the sharded students database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add one student")
    add_parser.add_argument("--student-id", required=True)
    add_parser.add_argument("--full-name", required=True)
    add_parser.add_argument("--group", required=True)
    add_parser.add_argument("--faculty", required=True)
    add_parser.add_argument("--admission-year", required=True, type=int)
    add_parser.set_defaults(func=add_student)

    get_parser = subparsers.add_parser("get", help="Get one student by student_id")
    get_parser.add_argument("--student-id", required=True)
    get_parser.set_defaults(func=get_student)

    list_parser = subparsers.add_parser("list", help="List students")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.set_defaults(func=list_students)

    seed_parser = subparsers.add_parser("seed", help="Seed synthetic students")
    seed_parser.add_argument("--count", type=int, default=1000)
    seed_parser.set_defaults(func=seed_students)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
