import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('library.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS Book (isbn TEXT PRIMARY KEY,title TEXT,author TEXT,genre TEXT,status_ TEXT,quantity INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS Member (member_id TEXT PRIMARY KEY,member_name TEXT,email TEXT,active_borrows INTEGER,fines INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS BorrowRecord (record_id INTEGER PRIMARY KEY AUTOINCREMENT,member_id TEXT,isbn TEXT,issueDate TEXT,dueDate TEXT,returnDate TEXT)")
conn.commit()
class Library:
    def borrow_book(self, member_id, isbn):
        c.execute("SELECT * FROM Member WHERE member_id=?", (member_id,))
        m = c.fetchone()
        if not m:
            print("invalid member")
            return
        if m[3] >= 3:
            print("borrow limit reached")
            return
        c.execute("SELECT * FROM Book WHERE isbn=?", (isbn,))
        b = c.fetchone()
        if not b:
            print("invalid isbn")
            return
        if b[5] <= 0 or b[4] == "NOT AVAILABLE":
            print("not available")
            return

        issue = datetime.now()
        due = issue + timedelta(days=7)

        c.execute("INSERT INTO BorrowRecord(member_id,isbn,issueDate,dueDate,returnDate) VALUES (?,?,?,?,?)",
                  (member_id, isbn, issue.isoformat(), due.isoformat(), None))

        c.execute("UPDATE Book SET quantity=quantity-1,status_='ISSUED' WHERE isbn=?", (isbn,))
        c.execute("UPDATE Member SET active_borrows=active_borrows+1 WHERE member_id=?", (member_id,))
        conn.commit()

        print("book issued")

    def return_book(self, member_id, isbn):
        c.execute("SELECT * FROM BorrowRecord WHERE member_id=? AND isbn=? AND returnDate IS NULL",
                  (member_id, isbn))
        r = c.fetchone()

        if not r:
            print("no record")
            return

        return_date = datetime.now()
        due = datetime.fromisoformat(r[4])
        delay = (return_date - due).days

        fine = 0
        if delay > 0:
            fine = delay * 10
            if fine > 100:
                fine = 100

        c.execute("UPDATE BorrowRecord SET returnDate=? WHERE record_id=?",
                  (return_date.isoformat(), r[0]))

        c.execute("UPDATE Book SET quantity=quantity+1,status_='AVAILABLE' WHERE isbn=?", (isbn,))
        c.execute("UPDATE Member SET active_borrows=active_borrows-1,fines=fines+? WHERE member_id=?",
                  (fine, member_id))
        conn.commit()
        print("returned", "fine =", fine)

if __name__ == "__main__":
    library = Library()
    c.execute("INSERT OR IGNORE INTO Book VALUES ('001','PYTHON','SUMITA','CS','AVAILABLE',2)")
    c.execute("INSERT OR IGNORE INTO Book VALUES ('002','MARVEL','STAN','MCU','AVAILABLE',1)")
    c.execute("INSERT OR IGNORE INTO Member VALUES ('1','KARUNYA','karunya@gmail.com',0,0)")
    conn.commit()
    library.borrow_book('1','001')
    library.borrow_book('1','002')
    library.borrow_book('1','003')
    library.return_book('1','001')
    conn.close()