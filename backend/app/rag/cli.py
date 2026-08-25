import argparse
import asyncio
from pathlib import Path

from app.database.session import session_factory
from app.rag.ingestion import ingest_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Lenny transcript files into PostgreSQL/pgvector")
    parser.add_argument("corpus", type=Path, help="Transcript file or directory")
    args = parser.parse_args()

    async def run() -> None:
        async with session_factory() as session:
            stats = await ingest_corpus(session, args.corpus)
            print(f"documents={stats.documents} chunks={stats.chunks} inserted_or_updated={stats.inserted_or_updated}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
