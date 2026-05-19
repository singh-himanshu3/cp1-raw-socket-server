# CP1: Raw Socket Server

A single-threaded, multi-client chat server built with raw Python sockets and `select()`. No asyncio, no threading, no third-party libraries. This is an OS-level event loop implemented from scratch.

---

## What It Does

The server accepts multiple simultaneous client connections over TCP and broadcasts messages between them in real time. When one client sends a message, every other connected client receives it instantly. The server handles client disconnections gracefully without crashing or affecting other active connections. It runs indefinitely on a single thread without blocking.

---

## How select() Works Here

The core of the server is a single call to `select.select()` inside an infinite loop. At the start, the server adds its own listening socket to a list called `inputs`. On every iteration of the loop, `select()` hands this list to the OS kernel and says: watch these file descriptors and tell me which ones have data ready right now.

The OS does the waiting. The server does nothing until `select()` returns. When it does return, it gives back only the sockets that are ready to be read without blocking. The server then iterates over that list. If the ready socket is the server socket itself, it means a new client is connecting, so the server accepts the connection and adds the new socket to `inputs`. If the ready socket is a client socket, it means that client sent a message, so the server reads it with `recv()` and broadcasts it to all other connected clients using `sendall()`.

When a client disconnects, `recv()` returns empty bytes or raises an `OSError`. Either way, the server removes that socket from `inputs` and closes it so `select()` never watches it again.

---

## Why Not Threading

Threading would work for this use case, but it adds unnecessary complexity. Each thread needs its own stack, and shared state like the client list requires locks to prevent race conditions. Context switching between threads has overhead. For I/O-bound tasks like a chat server, where most of the time is spent waiting for data rather than computing, a single-threaded `select()` loop is more efficient and simpler to reason about.

This is the same architecture that underlies Node.js, nginx, and Python's own asyncio. Those frameworks add abstractions and nicer syntax on top, but the core mechanism is identical: one thread, OS-managed waiting, act only when a socket is ready.

---

## How to Run

**Requirements:** Python 3.x, netcat (`nc`)

**Start the server:**
```bash
python3 server.py
```

**Connect clients (open separate terminals for each):**
```bash
nc localhost 8080
```

**Test broadcast:**
Type a message in any client terminal. All other connected terminals will receive it.

**Test disconnect handling:**
Close any client terminal with `Ctrl+C`. The server will log the disconnect and continue serving all other clients without interruption.

**Pass criteria:**
- 5 terminals connected simultaneously
- Message from terminal 1 appears in terminals 2-5
- Killing any terminal does not crash the server
- New clients can connect at any time and immediately receive broadcasts

---

## File Structure

```
CheckPoint1/
    server.py       # Single-file server implementation (~70 lines)
    README.md       # This file
```

---

## Key Concepts Demonstrated

- TCP socket creation, binding, and listening
- Non-blocking I/O with `setblocking(False)`
- OS-level I/O multiplexing via `select()`
- File descriptors and why sockets are treated as files in Unix
- Graceful and abrupt client disconnect handling
- Single-threaded concurrency for I/O-bound workloads
