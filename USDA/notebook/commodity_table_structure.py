# coding: utf-8
from sqlalchemy import BigInteger, Column, MetaData, Table, Text
from sqlalchemy.ext.declarative import declarative_base


metadata = MetaData()



t_commodity = Table(
    'commodity', metadata,
    Column('index', BigInteger, index=True),
    Column('commodity_code', BigInteger),
    Column('commodity_name', Text)
)
