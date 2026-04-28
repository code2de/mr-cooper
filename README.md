# Library Management System

## Problem Statement

Managing a library manually is time-consuming and error-prone. Tracking which books are available, which members have borrowed them, whether returns are overdue, and calculating fines — all of this becomes hard to maintain without a system in place.

This project solves that by building a simple web-based Library Management System where a librarian can issue books to members, accept returns, automatically calculate overdue fines, and view the current status of all books and members in one place.

---

## Approach and Logic

The system is built using **Python (Flask)** for the web layer and **SQLite** for data storage. The logic is organized using Object-Oriented Programming with the following classes:

- **`FinePolicy`** — Computes the fine based on how many days overdue a return is.
  - 0 days → ₹0
  - 1–7 days → ₹2 per day
  - 8–15 days → ₹5 per day
  - 16+ days → ₹10 per day

- **`Book`** — Checks whether a book is available (quantity > 0) and updates its status and quantity when issued or returned.

- **`Member`** — Handles inserting a borrow record and updating active borrow count when borrowing, and updating fines when returning.

- **`BorrowRecord`** — Represents an active borrow entry. Checks if it is overdue, calculates the fine using `FinePolicy`, and stamps the return date.

- **`Librarian`** — The main controller. Validates member and book before issuing, coordinates all objects during borrow and return, and handles adding or removing books.

**Borrow flow:**
1. Validate member exists and is under the 3-book limit.
2. Validate book exists and has available quantity.
3. Create a borrow record with issue date and due date (issue date + 7 days).
4. Decrease book quantity and increment member's active borrow count.

**Return flow:**
1. Find the active borrow record for that member and book.
2. Stamp the return date.
3. Calculate overdue days and fine.
4. Increase book quantity, decrement active borrows, and add fine to member record.

---

## Steps to Execute

**Step 1 — Make sure Python is installed**

```
python --version
```

**Step 2 — Install Flask**

```
pip install flask
```

**Step 3 — Run the application**

```
python library.py
```

**Step 4 — Open in browser**

```
http://127.0.0.1:5000
```

The database (`library.db`) is created automatically on first run with two sample books and one member preloaded.

---

## Project Structure

```
library.py       - main application (all classes, routes, and HTML)
library.db       - SQLite database (auto-created on first run)
```

## Classes and Methods

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
