from myapp.models import StockRecommendation
from django.db import connection

model = StockRecommendation
table_name = model._meta.db_table

with connection.cursor() as cursor:
    cursor.execute(f"""
        SELECT column_name, is_nullable, column_default, data_type
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()

print("--- SCHEMA START ---")
for col in columns:
    print(f"Column: {col[0]}, Nullable: {col[1]}, Default: {col[2]}, Type: {col[3]}")
print("--- SCHEMA END ---")
