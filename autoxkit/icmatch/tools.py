

class RectTuple(tuple):
    """
    矩形元组类，确保参数满足以下要求：
    1. 包含4个int类型元素
    2. 第三个元素必须大于第一个元素（x2 > x1）
    3. 第四个元素必须大于第二个元素（y2 > y1）
    """
    def __new__(cls, x1: int, y1: int, x2: int, y2: int):
        """
        创建新的RectTuple实例

        参数:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标
        """

        # 检查大小关系
        if x2 <= x1:
            raise ValueError(f"x2必须大于x1，当前 x1={x1}, x2={x2}")

        if y2 <= y1:
            raise ValueError(f"y2必须大于y1，当前 y1={y1}, y2={y2}")

        # 创建tuple实例
        return super().__new__(cls, (x1, y1, x2, y2))

    @property
    def x1(self):
        """返回左上角x1坐标"""
        return self[0]

    @property
    def y1(self):
        """返回左上角y1坐标"""
        return self[1]

    @property
    def x2(self):
        """返回右下角x2坐标"""
        return self[2]

    @property
    def y2(self):
        """返回右下角y2坐标"""
        return self[3]

    def __repr__(self):
        """返回对象的字符串表示"""
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"

