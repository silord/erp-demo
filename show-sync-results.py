import sync_store
from tabulate import tabulate

rows = sync_store.list_results(50)
if not rows:
    print('No sync results found.')
else:
    headers = ['id', 'bill_key', 'erp_key', 'sync_state', 'sync_msg', 'error_code', 'created_at']
    print(tabulate(rows, headers=headers, tablefmt='github'))
