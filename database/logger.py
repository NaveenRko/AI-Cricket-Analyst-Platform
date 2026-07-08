from database.supabase_client import supabase

def save_query(data):

    supabase.table("query_logs").insert(data).execute()