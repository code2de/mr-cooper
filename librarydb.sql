DROP TABLE IF EXISTS BorrowRecord;
DROP TABLE IF EXISTS Member;
DROP TABLE IF EXISTS Book;

CREATE TABLE Book (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT NOT NULL,
    status_ TEXT NOT NULL,
    quantity INTEGER NOT NULL
);

CREATE TABLE Member (
    member_id TEXT PRIMARY KEY,
    member_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    active_borrows INTEGER DEFAULT 0,
    fines INTEGER DEFAULT 0
);

CREATE TABLE BorrowRecord (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id TEXT NOT NULL,
    isbn TEXT NOT NULL,
    issueDate TEXT NOT NULL,
    dueDate TEXT NOT NULL,
    returnDate TEXT,
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (isbn) REFERENCES Book(isbn)
);