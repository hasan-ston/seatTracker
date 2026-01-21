I have configured a gunicorn master (PID 249181) that manages 2 gunicorn workers, PID 249184 and PID 249185. Each worker is an instance of the Flask app.

Having 2 workers allows for 2 simultaneous requests.

The master spawns the 2 workers on startup, monitors their health, automatically restarts workers if needed, and replaces workers that become unresponsive.

Acts as an internal request distributor; after accepting a connection from nginx, the gunicorn master coordinates which worker handles the request.

Health monitoring: workers periodically check the master using getppid() = 249181. If the master dies, workers exit and systemd restarts the service.

Following is an actual request trace from Worker 249184:
# Worker wakes up as request detected
pselect6(8, [5 7], NULL, NULL, {tv_sec=60...}) = 1 (in [5])

# Try to acquire the accept mutex
fchmod(6, 000) = 0

# SUCCESS! Accept the connection
accept4(5, {sa_family=AF_INET, sin_port=htons(40464),
        sin_addr=inet_addr("127.0.0.1")}, [16], SOCK_CLOEXEC) = 9

# Read the HTTP request (190 bytes)
recvfrom(9, "GET / HTTP/1.0\r\nHost: macseats.d"..., 8192, 0, NULL, NULL) = 190

# Flask routes to landing page - open template
openat(AT_FDCWD, "/home/ubuntu/seatTracker/backend/../frontend/user_templates/landing.html",
       O_RDONLY|O_CLOEXEC) = 10
read(10, "{% extends \"base.html\" %}\n\n{% bl"..., 4136) = 4135
close(10) = 0

# Load base template (Jinja2 inheritance)
openat(AT_FDCWD, "/home/ubuntu/seatTracker/backend/../frontend/user_templates/base.html",
       O_RDONLY|O_CLOEXEC) = 10
read(10, "<!DOCTYPE html>\n<html lang=\"en\">"..., 2534) = 2533
close(10) = 0

# Allocate memory for rendering
brk(0xdd64000) = 0xdd64000

# Send HTTP headers (169 bytes)
sendto(9, "HTTP/1.0 200 OK\r\nServer: gunicor"..., 169, 0, NULL, 0) = 169

# Send HTML body (5,463 bytes)
sendto(9, "<!DOCTYPE html>\n<html lang=\"en\">"..., 5463, 0, NULL, 0) = 5463

# Close connection
close(9) = 0

# Release accept mutex and go back to waiting
fchmod(6, 001) = 0
pselect6(8, [5 7], NULL, NULL, {tv_sec=60...}, NULL)


To summarize: both workers attempt to acquire the accept mutex. The worker that fails (accept4(...) = -1 with EAGAIN) releases the mutex and goes back to waiting via pselect6(...). The worker that succeeds accepts the connection, processes the request, releases the mutex, and then returns to the waiting state.

Nginx Configuration:

Process manager: systemd services
Web server: nginx (reverse proxy)

Benefits:

SSL/TLS termination handled at nginx.

Static file serving handled by nginx (significantly faster than Flask). Flask workers are freed to handle dynamic workloads such as database queries and scraping logic.

Load distribution across gunicorn workers, with the gunicorn master coordinating which worker processes each request.

Request buffering: nginx receives slow or fragmented client data, buffers the full request, and forwards it to Flask only once complete. This prevents Flask workers from being blocked by long-lived connections (e.g., 30-second uploads).

Security headers enforced at the proxy layer.

Enables scaling to multiple backend servers and avoids a single point of failure. If one worker is busy scraping a course, the other worker continues serving new requests.

DDoS mitigation via rate limiting and per-IP connection limits.
