from sqlalchemy import Column, Integer, String
from .models_init import Base


class ZlinkNode(Base):
    """
    author: Evren Keskin
    ZLinkNode class (ZLINKNODE table)

    Describe a ZLinkNode, which is composed of the primary key,
    the link node id, and the host name of the link

    Properties:
    z_pk: primary key of this link node entry
    zlinknodeid: the id of the related link node
    zhostname: the string name of the host of the link node

    Relationships:
    --- None

    """
    __tablename__ = 'ZLINKNODE'

    Z_PK = Column('Z_PK', Integer, primary_key=True)
    ZLINKNODEID = Column('ZLINKNODEID', Integer)
    ZHOSTNAME = Column('ZHOSTNAME', String)
