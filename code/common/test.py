import numpy


# (AB,AM), where M(X,Y) is the query point:
#
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.x} {self.y}"

# line
A = Point(0, 0)
B = Point(1, 1)

# points to check
p0 = Point(1, 0)
p1 = Point(-1, 0)
p2 = Point(0, 1)
p3 = Point(0, -1)

p4 = Point(1, 1)
p5 = Point(-1, 1)
p6 = Point(-1, -1)
p7 = Point(1, -1)

p_list = [p0, p1, p2, p3, p4, p5, p6, p7]

def is_point_left_of_vector(A, B, M):
    position = numpy.sign((B.x - A.x) * (M.y - A.y) - (B.y - A.y) * (M.x - A.x))
    print(M, ':', position)
    return position



for p in p_list:
    is_point_left_of_vector(A, B, p)