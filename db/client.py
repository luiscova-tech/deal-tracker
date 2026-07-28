"""Supabase client setup."""
import os

from supabase import Client, create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_client() -> Client | None:
    """
    Return a configured Supabase client, or None if credentials aren't set.

    Returning None (rather than raising) lets the rest of the app run against
    fake in-memory data before a Supabase project exists — see db/repository.py.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)
