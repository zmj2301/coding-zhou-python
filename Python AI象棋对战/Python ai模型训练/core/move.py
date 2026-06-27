# 走法表示与生成
from enum import Enum


class PieceType(Enum):
    """棋子类型枚举"""
    EMPTY = 0
    KING = 1
    ADVISOR = 2
    ELEPHANT = 3
    HORSE = 4
    CHARIOT = 5
    CANNON = 6
    PAWN = 7


class Color(Enum):
    """颜色/阵营"""
    RED = 0
    BLACK = 1


class Move:
    """走法表示"""
    def __init__(self, from_row, from_col, to_row, to_col):
        self.from_row = from_row
        self.from_col = from_col
        self.to_row = to_row
        self.to_col = to_col
    
    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return (self.from_row == other.from_row and
                self.from_col == other.from_col and
                self.to_row == other.to_row and
                self.to_col == other.to_col)
    
    def __repr__(self):
        return f"Move({self.from_row},{self.from_col}->{self.to_row},{self.to_col})"
    
    def to_ucci(self):
        """转换为UCCI协议格式"""
        cols = 'abcdefghi'
        rows = '0123456789'
        return (cols[self.from_col] + rows[9 - self.from_row] +
                cols[self.to_col] + rows[9 - self.to_row])
    
    @classmethod
    def from_ucci(cls, ucci_str):
        """从UCCI协议格式解析"""
        cols = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7,'i':8}
        rows = {'0':9,'1':8,'2':7,'3':6,'4':5,'5':4,'6':3,'7':2,'8':1,'9':0}
        return cls(rows[ucci_str[1]], cols[ucci_str[0]],
                   rows[ucci_str[3]], cols[ucci_str[2]])
