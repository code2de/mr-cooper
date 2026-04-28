from flask import Flask,request,render_template_string
import sqlite3
from datetime import datetime,timedelta

app=Flask(__name__)

def get_conn():
    return sqlite3.connect('library.db')

def setup():
    con=get_conn()
    c=con.cursor()
    c.execute("DROP TABLE IF EXISTS BorrowRecord")
    c.execute("DROP TABLE IF EXISTS Member")
    c.execute("DROP TABLE IF EXISTS Book")

    c.execute("CREATE TABLE Book(isbn TEXT PRIMARY KEY,title TEXT,author TEXT,genre TEXT,status_ TEXT,quantity INTEGER)")
    c.execute("CREATE TABLE Member(member_id TEXT PRIMARY KEY,member_name TEXT,email TEXT,active_borrows INTEGER,fines INTEGER)")
    c.execute("CREATE TABLE BorrowRecord(record_id INTEGER PRIMARY KEY AUTOINCREMENT,member_id TEXT,isbn TEXT,issueDate TEXT,dueDate TEXT,returnDate TEXT)")
    con.commit()
    con.close()

class Library:
    def borrow(self,mid,isbn):
        con=get_conn()
        c=con.cursor()

        c.execute("SELECT * FROM Member WHERE member_id=?",(mid,))
        m=c.fetchone()
        if not m:
            return "invalid member"

        if m[3]>=3:
            return "borrow limit reached"

        c.execute("SELECT * FROM Book WHERE isbn=?",(isbn,))
        b=c.fetchone()
        if not b:
            return "invalid isbn"

        if b[5]<=0:
            return "not available"

        issue=datetime.now()
        due=issue+timedelta(days=7)

        c.execute("INSERT INTO BorrowRecord(member_id,isbn,issueDate,dueDate,returnDate) VALUES(?,?,?,?,?)",
                  (mid,isbn,issue.isoformat(),due.isoformat(),None))

        c.execute("UPDATE Book SET quantity=quantity-1,status_='ISSUED' WHERE isbn=?",(isbn,))
        c.execute("UPDATE Member SET active_borrows=active_borrows+1 WHERE member_id=?",(mid,))
        con.commit()
        con.close()
        return "book issued"

    def return_book(self,mid,isbn):
        con=get_conn()
        c=con.cursor()

        c.execute("SELECT * FROM BorrowRecord WHERE member_id=? AND isbn=? AND returnDate IS NULL",(mid,isbn))
        r=c.fetchone()
        if not r:
            return "no record"

        ret=datetime.now()
        due=datetime.fromisoformat(r[4])

        delay=(ret-due).days
        if delay<0:
            delay=0

        fine=0
        if delay>0:
            if delay<=7:
                fine=delay*2
            elif delay<=15:
                fine=delay*5
            else:
                fine=delay*10

        c.execute("UPDATE BorrowRecord SET returnDate=? WHERE record_id=?",(ret.isoformat(),r[0]))
        c.execute("UPDATE Book SET quantity=quantity+1,status_='AVAILABLE' WHERE isbn=?",(isbn,))
        c.execute("UPDATE Member SET active_borrows=active_borrows-1,fines=fines+? WHERE member_id=?",(fine,mid))
        con.commit()
        con.close()

        return f"returned | overdue days = {delay} | fine = {fine}"

lib=Library()

html="""
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
<td><font face="Arial" size="2">Member ID:</font></td>
<td><input type="text" name="id" form="borrow_form" style="border:1px solid gray; padding:2px;"></td>
</tr>
<tr>
<td><font face="Arial" size="2">Book ISBN:</font></td>
<td><input type="text" name="isbn" form="borrow_form" style="border:1px solid gray; padding:2px;"></td>
</tr>
<tr>
<td colspan="2" align="center">
<form id="borrow_form" action="/borrow" method="get">
<input type="hidden" name="id" id="b_id">
<input type="hidden" name="isbn" id="b_isbn">
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
    con=get_conn()
    c=con.cursor()

    c.execute("""
    SELECT b.isbn,b.title,b.status_,b.quantity,
    CASE 
    WHEN br.dueDate IS NOT NULL AND br.returnDate IS NULL 
    THEN MAX(0, CAST((julianday('now') - julianday(br.dueDate)) AS INT))
    ELSE 0 END
    FROM Book b
    LEFT JOIN BorrowRecord br ON b.isbn=br.isbn
    GROUP BY b.isbn
    """)
    books=c.fetchall()

    c.execute("SELECT member_id,member_name,active_borrows,fines FROM Member")
    members=c.fetchall()

    con.close()
    return render_template_string(html,books=books,members=members,msg=msg)

@app.route("/")
def home():
    return render_home()

@app.route("/borrow")
def borrow():
    msg=lib.borrow(request.args.get("id"),request.args.get("isbn"))
    return render_home(msg)

@app.route("/return")
def ret():
    msg=lib.return_book(request.args.get("id"),request.args.get("isbn"))
    return render_home(msg)

if __name__=="__main__":
    setup()
    con=get_conn()
    c=con.cursor()
    c.execute("INSERT INTO Book VALUES('001','PYTHON','SUMITA','CS','AVAILABLE',2)")
    c.execute("INSERT INTO Book VALUES('002','MARVEL','STAN','MCU','AVAILABLE',1)")
    c.execute("INSERT INTO Member VALUES('1','KARUNYA','karunya@gmail.com',0,0)")
    con.commit()
    con.close()
    app.run(debug=True)