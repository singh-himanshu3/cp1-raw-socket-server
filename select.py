import socket
import select

HOST = '127.0.0.1'
PORT = 8080

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    
    
    # Allows reusing PORT 8080 immediately after server restart.
    # Without this, OS keeps port in TIME_WAIT state and throws "Address already in use" error.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST,PORT))
    server_socket.listen(5)

    # Prevents server socket from freezing on accept() if no client arrives.
    # Non-blocking means select() stays in control — accept() never waits.
    server_socket.setblocking(False)
    print(f"Server listening on PORT {PORT}")

    inputs = [server_socket]

    while True: 

        # select() takes 3 lists: sockets to watch for read, write, and errors.
        # We only care about reading — wlist and xlist are empty because
        # we never need to wait for a socket to be writable or catch exceptions here.
        readable, writable, exceptional = select.select(inputs,[],[])

        for read in readable:

            if read is server_socket:
                conn,addr = server_socket.accept()
                print(f"New Connection from {addr}")
                
                # Prevents client socket from freezing on recv() or send().
                # If blocking, one slow client would freeze the entire server loop.
                conn.setblocking(False)
                inputs.append(conn)

            else:
                try:

                    # Must call getpeername() before recv() so addr is always defined.
                    # If recv() raises OSError, we still need addr to log which client disconnected.
                    addr,port = read.getpeername()

                    # Read up to 1024 bytes from the client.
                    # 1024 is enough for chat messages — large enough for typical input, small enough to avoid memory waste.
                    data = read.recv(1024)
                    
                    if data:
                        message = f"{addr} says: {data.decode('utf-8')}".encode('utf-8')
                        for all_socket in inputs:
                            
                            # Skip server_socket — it is a listening socket, cannot receive chat messages.
                            # Skip read (the sender) — we don't want messages echoed back to the client who sent them.
                            if all_socket is server_socket or all_socket is read:
                                continue
                            else:
                                try:
                                    all_socket.sendall(message)      
                                except OSError:
                                    print(f"{addr} skipped")
                    else:
                        print(f"{addr} disconnected")

                        # Remove dead socket from inputs so select() never watches it again.
                        # Without this, select() would return it as readable forever, causing an infinite loop of empty reads.
                        inputs.remove(read)

                        # Explicitly close the socket to free the file descriptor immediately.
                        # Without this, OS holds the resource open until garbage collection — wastes file descriptors.
                        read.close()
                
                except OSError:
                    print(f"{addr} is disconnected")
                    inputs.remove(read)
                    read.close()

