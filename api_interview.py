import pandas as pd

# 1. Retry decorator for API stability
@retry(exponential_backoff, max_retries=5)
def fetch_api_page(cursor_id):
    # Calls API, handles 429s/timeouts
    # Returns a list of dictionaries and the next cursor
    return json_data_list, next_cursor 

# 2. Generator to manage memory and convert to Pandas
def extract_ticket_batches(start_cursor, batch_size=10000):
    current_cursor = start_cursor
    buffer = []
    
    while current_cursor:
        json_data_list, current_cursor = fetch_api_page(current_cursor)
        buffer.extend(json_data_list)
        
        # ONCE the buffer hits our memory limit, convert to Pandas
        if len(buffer) >= batch_size:
            df_chunk = pd.DataFrame(buffer) # <--- JSON to Pandas happens here
            yield df_chunk
            buffer = [] # Clear the buffer to free up memory
            
    # Yield any remaining records in the buffer after the loop finishes
    if buffer:
        yield pd.DataFrame(buffer)

# 3. Idempotent load
def load_to_azure(execution_date):
    # Loop through the yielded DataFrames and write each as a Parquet file
    for index, df_chunk in enumerate(extract_ticket_batches(start_cursor=None)):
        
        # Write to Bronze layer partition, e.g., raw/tickets/date=2026-09-30/chunk_1.parquet
        file_path = f"abfss://datalake/raw/tickets/date={execution_date}/chunk_{index}.parquet"
        
        df_chunk.to_parquet(file_path)
