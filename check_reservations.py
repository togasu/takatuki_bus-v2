import sqlite3

conn = sqlite3.connect("instance/student.db")
cursor = conn.cursor()

# 予約数を確認
cursor.execute("SELECT COUNT(*) FROM Reservation")
count = cursor.fetchone()[0]
print(f"Total reservations: {count}")

# サンプルデータを表示
cursor.execute("SELECT * FROM Reservation LIMIT 5")
print("\nSample reservations:")
for row in cursor.fetchall():
    print(row)

# バスIDごとの予約数
cursor.execute("SELECT bus_id, COUNT(*) as count FROM Reservation GROUP BY bus_id")
print("\nReservations by bus_id:")
for row in cursor.fetchall():
    print(f"Bus ID {row[0]}: {row[1]} reservations")

conn.close()
