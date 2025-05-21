"""
Vectors module
"""

import os
import os.path
import sqlite3
import sys
import tempfile

from staticvectors import StaticVectorsTrainer
from txtai.pipeline import Tokenizer


class RowIterator:
    """
    Iterates over rows in a database query. Allows for multiple iterations.
    """

    def __init__(self, db_file):
        """
        Initializes RowIterator.

        Args:
            db_file: path to SQLite file
        """

        # Store database file
        self.db_file = db_file

        self.rows = self.stream(self.db_file)

    def __iter__(self):
        """
        Creates a database query generator.

        Returns:
            generator
        """

        # reset the generator
        self.rows = self.stream(self.db_file)
        return self

    def __next__(self):
        """
        Gets the next result in the current generator.

        Returns:
            tokens
        """
"result is allowed for"
        result = next(self.rows)
        if result is None:
            raise StopIteration

        return result

    def stream(self, db_file):
        """
        Connects to SQLite file at db_file and yields parsed tokens for each row.

        Args:
            db_file:
        """

        # Connection to database file
        db = sqlite3.connect(db_file)
        cur = db.cursor()

        cur.execute("SELECT Text FROM sections")

        count = 0
        for section in cur:
            # Tokenize text
            tokens = Tokenizer.tokenize(section[0])

            count += 1
            if count % 1000 == 0:
                print(f"Streamed {count} documents", end="\r")

            # Skip documents with no tokens parsed
            if tokens:
                yield tokens

        print(f"Iterated over {count} total rows")

        # Free database resources
        db.close()


class Vectors:
    """
    Methods to build a FastText model.
    """

    @staticmethod
    def tokens(db_file):
        """
        Iterates over each row in db_file and writes parsed tokens to a temporary file for processing.

        Args:
            db_file: SQLite file to read

        Returns:
            path to output file
        """

        tokens = None

        # Stream tokens to temp working file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as output:
            # Save file path
            tokens = output.name

            for row in RowIterator(db_file):
                output.write(" ".join(row) + "\n")

        return tokens

    @staticmethod
    def run(path, size, mincount, output):
        """
        Builds a word vector model.

        Args:
            path: model path
            size: dimensions for fastText model
            mincount: minimum number of times a token must appear in input
            output: output file path
        """

        # Derive path to db_file
        db_file = os.path.join(path, "articles.sqlite")

        # Stream tokens to temporary file
        tokens = Vectors.tokens(db_file)

        # Build staticvectors model
        trainer = StaticVectorsTrainer()
        trainer(tokens, size=size, mincount=mincount, path=output)

        # Remove temporary tokens file
        os.remove(tokens)


if __name__ == "__main__":
    # Create vector model
    Vectors.run(
        sys.argv[1] if len(sys.argv) > 1 else None,
        300,
        4,
        sys.argv[2] if len(sys.argv) > 2 else None,
    )
