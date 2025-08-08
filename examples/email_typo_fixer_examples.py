"""
Examples for efficient bulk email normalization using EmailTypoFixer.
Includes single-threaded and multiprocessing usage.
"""

import multiprocessing as mp
from email_typo_fixer import EmailTypoFixer, setup_logging


# --- Basic single-threaded usage ---

def normalize_bulk(emails):
    fixer = EmailTypoFixer()
    results = []
    for email in emails:
        try:
            results.append(fixer.normalize(email))
        except ValueError:
            results.append(None)
    return results


# --- Multiprocessing usage ---

def worker(email_chunk):
    fixer = EmailTypoFixer()  # Each process gets its own instance
    out = []
    for email in email_chunk:
        try:
            out.append(fixer.normalize(email))
        except ValueError:
            out.append(None)
    return out


def normalize_bulk_multiprocess(emails, nproc=4):
    chunk_size = (len(emails) + nproc - 1) // nproc
    chunks = [emails[i:i+chunk_size] for i in range(0, len(emails), chunk_size)]
    with mp.Pool(nproc) as pool:
        results = pool.map(worker, chunks)
    # Flatten results
    return [item for sublist in results for item in sublist]


if __name__ == "__main__":
    # Setup package logging (optional, for demonstration)
    setup_logging()

    # Example emails
    emails = [
        "User@Example.Com", "user@gamil.com", "bad@email", "user@outlok.com",
        "user@example.co", "user@site.rog", "user@gnail.com", "user@hotmal.com"
    ]

    print("Single-threaded:")
    print(normalize_bulk(emails))

    print("\nMultiprocessing:")
    print(normalize_bulk_multiprocess(emails, nproc=2))
