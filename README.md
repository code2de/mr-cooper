# Library Management System

A simple web-based library system built with Python (Flask) and SQLite.

## Requirements

```
pip install flask
```

## How to Run

```
python library.py
```

Then open your browser and go to `http://127.0.0.1:5000`

## Features

- Borrow and return books
- Fine calculation for overdue returns
- Borrow limit of 3 books per member
- Overdue day tracking on the home page

## Fine Policy

| Overdue Days | Fine per Day |
|---|---|
| 0 | ₹0 |
| 1 – 7 | ₹2 |
| 8 – 15 | ₹5 |
| 16+ | ₹10 |

## Project Structure

```
library.py       - main application file
library.db       - SQLite database (auto-created on first run)
```

## Classes

| Class | Methods |
|---|---|
| `FinePolicy` | `computefine(daysoverdue)` |
| `Book` | `checkavailability()`, `updatestatus(action)` |
| `Member` | `borrowbook(isbn)`, `returnbook(isbn, fine)`, `payfine(amount)` |
| `BorrowRecord` | `isoverdue()`, `calculatefine()`, `markreturn()` |
| `Librarian` | `issuebook(mid, isbn)`, `processreturn(mid, isbn)`, `addbook(...)`, `removebook(isbn)` |

## Default Data (loaded on startup)

**Books**
- `001` — PYTHON by SUMITA (qty: 2)
- `002` — MARVEL by STAN (qty: 1)

**Members**
- ID `1` — KARUNYA (karunya@gmail.com)
