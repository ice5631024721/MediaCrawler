# from infinity import infinity
from infinity import connect
from infinity.common import ConflictType

import infinity

# infinity_obj = connect("/Users/lingxiao.yz/program/infinity")
#
# infinity_obj.create_database('test', conflict_type = ConflictType.Error)
# infinity_obj.disconnect()


# # Connect to infinity
# infinity_obj = infinity.connect("localhost:23817//Users/lingxiao.yz/program/infinity")
# db = infinity_obj.get_database("default_db")
# table = db.create_table("my_table", {"num": {"type": "integer"}, "body": {"type": "varchar"}, "vec": {"type": "vector, 4, float"}})
# table.insert([{"num": 1, "body": "unnecessary and harmful", "vec": [1.0, 1.2, 0.8, 0.9]}])
# table.insert([{"num": 2, "body": "Office for Harmful Blooms", "vec": [4.0, 4.2, 4.3, 4.5]}])
# res = table.output(["*"]).knn("vec", [3.0, 2.8, 2.7, 3.1], "float", "ip", 2).to_pl()
# print(res)

# 连接到本地数据库
db = infinity.connect("localhost")

# 执行查询
results = db.execute("SELECT * FROM your_table")
for row in results:
    print(row)
