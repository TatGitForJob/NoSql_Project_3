import random
import time

from pymongo import MongoClient

from config import COLLECTION_NAME, DB_NAME, MONGO_URI


def main():
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    existing_count = collection.count_documents({})
    if existing_count == 0:
        raise SystemExit("benchmark requires seeded data; run 'python3 cli.py seed --count 1000' first")

    read_pool = min(existing_count, 1000)
    ids = [f"S{index:06d}" for index in range(read_pool)]
    start_index = existing_count

    start = time.perf_counter()
    for index in range(start_index, start_index + 5000):
        collection.insert_one(
            {
                "student_id": f"S{index:06d}",
                "full_name": f"Benchmark Student {index}",
                "group": "BENCH-1",
                "faculty": "Engineering",
                "admission_year": 2024,
            }
        )
    insert_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(1000):
        collection.find_one({"student_id": random.choice(ids)})
    read_time = time.perf_counter() - start

    print({"insert_5000_seconds": round(insert_time, 3), "read_1000_seconds": round(read_time, 3)})


if __name__ == "__main__":
    main()
