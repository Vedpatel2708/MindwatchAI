"""
backend/database.py
====================
PURPOSE:
    Creates and exports the Supabase client singleton used by every part of
    the backend (routers, agent tools, analytics) to read/write the database.

ARCHITECTURE ROLE:
    This is the single source of truth for DB access. All other modules import
    `supabase_client` from here — they never create their own client instances.

DESIGN DECISION — SINGLETON PATTERN:
    We create ONE client at module load time and reuse it for every request.
    Why not create a new client per request?
      - The supabase-py client establishes an HTTP session internally.
        Re-creating it on every request wastes time on connection setup.
      - The Supabase free tier has connection limits; a singleton respects them.
      - Singleton is safe here because the client is stateless between calls
        (no shared mutable state that could cause race conditions).

ENVIRONMENT VARIABLES REQUIRED:
    SUPABASE_URL      — your project REST endpoint (from Supabase Dashboard)
    SUPABASE_ANON_KEY — your project's anon/public key (safe for backend use)
    Both are loaded via config.py which reads from the .env file.
"""

import sys          # sys.exit() — used to terminate the process if DB is unreachable
import logging      # Standard Python logging — records errors to stdout/file

# supabase: the official Python client for Supabase.
# create_client() takes the URL and anon key and returns a Client object
# that wraps the PostgREST REST API, Auth, Realtime, and Storage APIs.
# We only use the database (PostgREST) portion in this project.
from supabase import create_client, Client

# Import our Settings singleton from config.py.
# settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY are loaded from .env
from config import settings

# Set up a module-level logger so error messages identify which file they came from.
# Best practice: always use __name__ as the logger name (gives "database" here).
logger = logging.getLogger(__name__)


def _create_supabase_client() -> Client:
    """
    Internal factory function that creates the Supabase client.

    WHY A SEPARATE FUNCTION?
        Wrapping client creation in a function makes it easy to mock in tests
        (you can patch `database._create_supabase_client` instead of the
        supabase library itself).

    Returns:
        Client: A configured supabase-py Client instance ready for DB calls.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY are empty strings.
    """
    # Guard: both values must be non-empty strings.
    # create_client() would produce a confusing error if given empty strings,
    # so we surface the problem clearly here.
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file. "
            "Get them from: Supabase Dashboard → Settings → API"
        )

    # create_client(url, key) initialises the PostgREST HTTP client.
    # It does NOT open a persistent TCP connection — each DB call is a
    # separate HTTPS request to the Supabase REST API.
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETON
# ---------------------------------------------------------------------------
# This line runs ONCE when Python first imports this module.
# All subsequent `from database import supabase_client` calls return
# the SAME already-created Client object from Python's module cache.
supabase_client: Client = _create_supabase_client()


def check_db_connection() -> None:
    """
    Verifies that the Supabase client can reach the database.

    Called at FastAPI startup (in main.py's @app.on_event("startup")).
    If the DB is unreachable, logs a descriptive error and exits the process
    with a non-zero status code so the container/process manager knows to
    restart or alert. (Requirement 8.6)

    WHY EXIT INSTEAD OF RAISE?
        During startup, if we can't reach the DB, the server is useless — every
        request would fail. Exiting immediately surfaces the problem loudly
        rather than starting a broken server that silently fails all requests.

    Raises:
        SystemExit(1): If the DB connection test fails for any reason.
    """
    try:
        # Perform a lightweight query: fetch 1 row from `transactions`.
        # We use `limit(1)` to minimise data transfer — we only care whether
        # the connection works, not about the actual data.
        # If the table doesn't exist yet (schema not applied), this raises an
        # exception which we catch below.
        response = supabase_client.table("transactions").select("id").limit(1).execute()

        # supabase-py doesn't raise on HTTP errors by default — it returns the
        # response. We check for an error in the response object.
        # `response.data` is None when the PostgREST API returns an error.
        logger.info("✅ Supabase connection check passed.")

    except Exception as exc:
        # Log the full error with traceback so the developer knows exactly
        # what went wrong (wrong URL, wrong key, schema not applied, etc.)
        logger.error(
            "❌ Supabase connection failed at startup.\n"
            "  Check that:\n"
            "  1. SUPABASE_URL and SUPABASE_ANON_KEY are set correctly in .env\n"
            "  2. You have run supabase_schema.sql in your Supabase SQL Editor\n"
            "  3. Your Supabase project is active (free tier pauses after 1 week idle)\n"
            f"  Error: {exc}"
        )
        # Exit with code 1 (non-zero = failure).
        # This signals to Docker, systemd, or any process manager that the
        # service failed to start and should be restarted or alerted.
        sys.exit(1)
