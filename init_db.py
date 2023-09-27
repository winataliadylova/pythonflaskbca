import sqlite3
from sqlalchemy import create_engine, Column, Integer, DECIMAL, DateTime, ForeignKey, String, MetaData, Table

DATABASE_URL = 'mysql://root:cX8fGXW19Keo2TaEYoJf@containers-us-west-88.railway.app:7042/railway'
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()

# Mendifinisikan table 'Master'
items = Table('items', metadata,
    Column('item_id', Integer, primary_key=True),
    Column('name', String),
    Column('category', String),
    Column('quantity', Integer),
    Column('price', DECIMAL(10,2))
)

# Mendifinisikan tabel 'Transaction'
transactions = Table('transactions', metadata,
    Column('transaction_id', Integer, primary_key=True),
    Column('item_id', Integer, ForeignKey('items.item_id')),
    Column('date', DateTime),
    Column('quantity', Integer),
    Column('total_price', DECIMAL(10,2))
)

# Membuat Table
metadata.create_all(engine)

print("Database invbar.db dan tabel Master dan tabel Transaction telah berhasil dibuat!")