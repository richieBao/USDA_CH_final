# coding: utf-8
from sqlalchemy import BigInteger, Column, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base


metadata = MetaData()



t_sale_details = Table(
    'sale_details', metadata,
    Column('index', BigInteger, index=True),
    Column('idx', BigInteger),
    Column('commodity_code', BigInteger),
    Column('number', BigInteger)
)
