import random
import time

from pymongo import MongoClient

from config import COLLECTION_NAME, DB_NAME, MONGO_URI

LOAD_COUNT = 10000
READ_COUNT = 50000
BATCH_SIZE = 1000


def build_student(index: int) -> dict:
    return {
        "student_id": f"S{index:06d}",
        "full_name": f"Benchmark Student {index}",
        "group": "BENCH-1",
        "faculty": "Engineering",
        "admission_year": 2024,
    }


def main():
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]
    collection.create_index("student_id", unique=True)

    start_index = collection.count_documents({})
    read_ids = [f"S{index:06d}" for index in range(start_index, start_index + LOAD_COUNT)]

    start = time.perf_counter()
    for batch_start in range(start_index, start_index + LOAD_COUNT, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, start_index + LOAD_COUNT)
        collection.insert_many([build_student(index) for index in range(batch_start, batch_end)])
    insert_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(READ_COUNT):
        collection.find_one({"student_id": random.choice(read_ids)})
    read_time = time.perf_counter() - start

    print(
        {
            f"insert_{LOAD_COUNT}_seconds": round(insert_time, 3),
            f"read_{READ_COUNT}_seconds": round(read_time, 3),
        }
    )


if __name__ == "__main__":
    main()
