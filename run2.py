from flask import Flask, request, render_template_string
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def get_conn():
    return sqlite3.connect('library.db')

def setup():
    con = get_conn()
    c = con.cursor()
    c.execute("DROP TABLE IF EXISTS BorrowRecord")
    c.execute("DROP TABLE IF EXISTS Member")
    c.execute("DROP TABLE IF EXISTS Book")
    c.execute("CREATE TABLE Book(isbn TEXT PRIMARY KEY, title TEXT, author TEXT, genre TEXT, status_ TEXT, quantity INTEGER)")
    c.execute("CREATE TABLE Member(member_id TEXT PRIMARY KEY, member_name TEXT, email TEXT, active_borrows INTEGER, fines INTEGER)")
    c.execute("CREATE TABLE BorrowRecord(record_id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT, isbn TEXT, issueDate TEXT, dueDate TEXT, returnDate TEXT)")
    con.commit()
    con.close()


class FinePolicy:
    def computefine(self, daysoverdue):
        if daysoverdue <= 0:
            return 0
        elif daysoverdue <= 7:
            return daysoverdue * 2
        elif daysoverdue <= 15:
            return daysoverdue * 5
        else:
            return daysoverdue * 10


class Book:
    def __init__(self, isbn):
        self.isbn = isbn

    def checkavailability(self):
        con = get_conn()
        c = con.cursor()
        c.execute("SELECT quantity FROM Book WHERE isbn=?", (self.isbn,))
        row = c.fetchone()
        con.close()
        if not row:
            return False
        return row[0] > 0

    def updatestatus(self, action):
        con = get_conn()
        c = con.cursor()
        if action == "issue":
            c.execute("UPDATE Book SET quantity=quantity-1, status_='ISSUED' WHERE isbn=?", (self.isbn,))
        elif action == "return":
            c.execute("UPDATE Book SET quantity=quantity+1, status_='AVAILABLE' WHERE isbn=?", (self.isbn,))
        con.commit()
        con.close()


class Member:
    def __init__(self, member_id):
        self.member_id = member_id

    def borrowbook(self, isbn):
        con = get_conn()
        c = con.cursor()
        c.execute("UPDATE Member SET active_borrows=active_borrows+1 WHERE member_id=?", (self.member_id,))
        issue = datetime.now()
        due = issue + timedelta(days=7)
        c.execute("INSERT INTO BorrowRecord(member_id, isbn, issueDate, dueDate, returnDate) VALUES(?,?,?,?,?)",
                  (self.member_id, isbn, issue.isoformat(), due.isoformat(), None))
        con.commit()
        con.close()

    def returnbook(self, isbn, fine):
        con = get_conn()
        c = con.cursor()
        c.execute("UPDATE Member SET active_borrows=active_borrows-1, fines=fines+? WHERE member_id=?", (fine, self.member_id))
        con.commit()
        con.close()

    def payfine(self, amount):
        con = get_conn()
        c = con.cursor()
        c.execute("UPDATE Member SET fines=MAX(0, fines-?) WHERE member_id=?", (amount, self.member_id))
        con.commit()
        con.close()


class BorrowRecord:
    def __init__(self, record_id, member_id, isbn, issue_date, due_date, return_date=None):
        self.record_id = record_id
        self.member_id = member_id
        self.isbn = isbn
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date

    def isoverdue(self):
        check = self.return_date if self.return_date else datetime.now()
        return check > self.due_date

    def calculatefine(self):
        policy = FinePolicy()
        check = self.return_date if self.return_date else datetime.now()
        delay = (check - self.due_date).days
        return policy.computefine(delay), max(0, delay)

    def markreturn(self):
        con = get_conn()
        c = con.cursor()
        ret = datetime.now()
        c.execute("UPDATE BorrowRecord SET returnDate=? WHERE record_id=?", (ret.isoformat(), self.record_id))
        con.commit()
        con.close()
        self.return_date = ret


class Librarian:
    def issuebook(self, mid, isbn):
        con = get_conn()
        c = con.cursor()
        c.execute("SELECT * FROM Member WHERE member_id=?", (mid,))
        mrow = c.fetchone()
        if not mrow:
            con.close()
            return "invalid member"
        if mrow[3] >= 3:
            con.close()
            return "borrow limit reached"
        c.execute("SELECT * FROM Book WHERE isbn=?", (isbn,))
        brow = c.fetchone()
        con.close()
        if not brow:
            return "invalid isbn"
        book = Book(isbn)
        if not book.checkavailability():
            return "not available"
        member = Member(mid)
        member.borrowbook(isbn)
        book.updatestatus("issue")
        return "book issued"

    def processreturn(self, mid, isbn):
        con = get_conn()
        c = con.cursor()
        c.execute("SELECT * FROM BorrowRecord WHERE member_id=? AND isbn=? AND returnDate IS NULL", (mid, isbn))
        row = c.fetchone()
        con.close()
        if not row:
            return "no record"
        record = BorrowRecord(
            record_id=row[0],
            member_id=row[1],
            isbn=row[2],
            issue_date=datetime.fromisoformat(row[3]),
            due_date=datetime.fromisoformat(row[4]),
            return_date=None
        )
        record.markreturn()
        fine, delay = record.calculatefine()
        member = Member(mid)
        member.returnbook(isbn, fine)
        book = Book(isbn)
        book.updatestatus("return")
        return f"returned | overdue days = {delay} | fine = {fine}"

    def addbook(self, isbn, title, author, genre, quantity):
        con = get_conn()
        c = con.cursor()
        c.execute("INSERT INTO Book VALUES(?,?,?,?,'AVAILABLE',?)", (isbn, title, author, genre, quantity))
        con.commit()
        con.close()

    def removebook(self, isbn):
        con = get_conn()
        c = con.cursor()
        c.execute("DELETE FROM Book WHERE isbn=?", (isbn,))
        con.commit()
        con.close()


librarian = Librarian()

html = """
<html>
<head>
<title>Library System</title>
</head>
<body bgcolor="#f0f0f0">

<center>
<font face="Times New Roman" size="6" color="darkblue">
<b>LIBRARY MANAGEMENT SYSTEM</b>
</font>
<br>
<font face="Times New Roman" size="2" color="gray">-- manage your books here --</font>
</center>

<br>

<center>
<table border="2" cellpadding="5" cellspacing="0" bgcolor="white" width="700">
<tr bgcolor="navy">
<td colspan="5"><font color="white" face="Arial" size="3"><b>BOOK LIST</b></font></td>
</tr>
<tr bgcolor="lightblue">
<th><font face="Arial" size="2">ISBN</font></th>
<th><font face="Arial" size="2">Title</font></th>
<th><font face="Arial" size="2">Status</font></th>
<th><font face="Arial" size="2">Qty</font></th>
<th><font face="Arial" size="2">Overdue Days</font></th>
</tr>
{% for b in books %}
<tr bgcolor="{% if loop.index is odd %}#ffffff{% else %}#eeeeee{% endif %}">
<td><font face="Arial" size="2">{{b[0]}}</font></td>
<td><font face="Arial" size="2">{{b[1]}}</font></td>
<td>
  {% if b[2] == 'AVAILABLE' %}
  <font face="Arial" size="2" color="green"><b>{{b[2]}}</b></font>
  {% else %}
  <font face="Arial" size="2" color="red"><b>{{b[2]}}</b></font>
  {% endif %}
</td>
<td align="center"><font face="Arial" size="2">{{b[3]}}</font></td>
<td align="center"><font face="Arial" size="2" color="{% if b[4] > 0 %}red{% else %}black{% endif %}">{{b[4]}}</font></td>
</tr>
{% endfor %}
</table>
</center>

<br>

<center>
<table border="2" cellpadding="5" cellspacing="0" bgcolor="white" width="700">
<tr bgcolor="navy">
<td colspan="4"><font color="white" face="Arial" size="3"><b>MEMBER LIST</b></font></td>
</tr>
<tr bgcolor="lightblue">
<th><font face="Arial" size="2">Member ID</font></th>
<th><font face="Arial" size="2">Name</font></th>
<th><font face="Arial" size="2">Active Borrows</font></th>
<th><font face="Arial" size="2">Fines (Rs.)</font></th>
</tr>
{% for m in members %}
<tr bgcolor="{% if loop.index is odd %}#ffffff{% else %}#eeeeee{% endif %}">
<td><font face="Arial" size="2">{{m[0]}}</font></td>
<td><font face="Arial" size="2">{{m[1]}}</font></td>
<td align="center"><font face="Arial" size="2">{{m[2]}}</font></td>
<td align="center"><font face="Arial" size="2" color="{% if m[3] > 0 %}red{% else %}black{% endif %}"><b>{{m[3]}}</b></font></td>
</tr>
{% endfor %}
</table>
</center>

<br>

<center>
<table border="2" cellpadding="8" cellspacing="0" bgcolor="white" width="700">
<tr bgcolor="navy">
<td colspan="2"><font color="white" face="Arial" size="3"><b>BORROW A BOOK</b></font></td>
</tr>
<tr>
<td colspan="2" align="center">
<form action="/borrow" method="get">
<input type="text" name="id" placeholder="Member ID" style="border:1px solid gray; padding:3px; width:120px;">
&nbsp;
<input type="text" name="isbn" placeholder="ISBN" style="border:1px solid gray; padding:3px; width:120px;">
&nbsp;
<input type="submit" value="Borrow" style="background-color:navy; color:white; padding:4px 10px; border:none; cursor:pointer;">
</form>
</td>
</tr>
</table>
</center>

<br>

<center>
<table border="2" cellpadding="8" cellspacing="0" bgcolor="white" width="700">
<tr bgcolor="darkgreen">
<td colspan="2"><font color="white" face="Arial" size="3"><b>RETURN A BOOK</b></font></td>
</tr>
<tr>
<td colspan="2" align="center">
<form action="/return" method="get">
<input type="text" name="id" placeholder="Member ID" style="border:1px solid gray; padding:3px; width:120px;">
&nbsp;
<input type="text" name="isbn" placeholder="ISBN" style="border:1px solid gray; padding:3px; width:120px;">
&nbsp;
<input type="submit" value="Return" style="background-color:darkgreen; color:white; padding:4px 10px; border:none; cursor:pointer;">
</form>
</td>
</tr>
</table>
</center>

<br>

{% if msg %}
<center>
<table border="1" cellpadding="6" bgcolor="lightyellow" width="400">
<tr>
<td align="center">
<font face="Arial" size="3" color="darkred"><b>Result: {{msg}}</b></font>
</td>
</tr>
</table>
</center>
<br>
{% endif %}

<center>
<font face="Arial" size="1" color="gray">Library System v1.0 &copy; 2024</font>
</center>

</body>
</html>
"""

def render_home(msg=""):
    con = get_conn()
    c = con.cursor()
    c.execute("""
    SELECT b.isbn, b.title, b.status_, b.quantity,
    CASE 
    WHEN br.dueDate IS NOT NULL AND br.returnDate IS NULL 
    THEN MAX(0, CAST((julianday('now') - julianday(br.dueDate)) AS INT))
    ELSE 0 END
    FROM Book b
    LEFT JOIN BorrowRecord br ON b.isbn = br.isbn
    GROUP BY b.isbn
    """)
    books = c.fetchall()
    c.execute("SELECT member_id, member_name, active_borrows, fines FROM Member")
    members = c.fetchall()
    con.close()
    return render_template_string(html, books=books, members=members, msg=msg)

@app.route("/")
def home():
    return render_home()

@app.route("/borrow")
def borrow():
    msg = librarian.issuebook(request.args.get("id"), request.args.get("isbn"))
    return render_home(msg)

@app.route("/return")
def ret():
    msg = librarian.processreturn(request.args.get("id"), request.args.get("isbn"))
    return render_home(msg)

if __name__ == "__main__":
    setup()
    con = get_conn()
    c = con.cursor()
    c.execute("INSERT INTO Book VALUES('001','PYTHON','SUMITA','CS','AVAILABLE',2)")
    c.execute("INSERT INTO Book VALUES('002','MARVEL','STAN','MCU','AVAILABLE',1)")
    c.execute("INSERT INTO Member VALUES('1','KARUNYA','karunya@gmail.com',0,0)")
    con.commit()
    con.close()
    app.run(debug=True)