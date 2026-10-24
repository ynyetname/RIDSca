# Security and privacy

RIDSca is a private-pilot research prototype. Treat every upload, QR payload,
message and model output as untrusted. No submitted URL is fetched, and no APK
is installed or executed. Parser processes use generated local filenames and
argument arrays rather than shell commands. FFmpeg/FFprobe are restricted to
local-file/pipe protocols. HTML scripts are not executed.

Limits, zip expansion checks, process timeouts and a non-root Docker image reduce
risk; they are not a complete sandbox. Parsing libraries and model runtimes may
have vulnerabilities. The container holds download/deployment credentials only
if an operator configures them; avoid unnecessary tokens. The public UI has no
per-user authentication or distributed rate limiting.

Uploaded bytes and results live in Streamlit session memory. Temporary files
use `TemporaryDirectory` and are removed after processing, including exceptions.
No input/result logging or training-data collection is implemented. Deletion
means reference/file removal, not guaranteed secure memory/disk erasure.
Idle TTL is checked on the next interaction. A disconnected session expires
according to Streamlit's 60-second setting. Hosting logs/infrastructure are not
controlled by this code. JSON exports can contain sensitive names/metadata or
unredacted values the simple redactor missed.

Model guardrails can miss non-English injection or share the generator's errors.
Deterministic output constraints, independent verification and explicit coverage
gaps remain necessary. Do not treat a low score as permission to make a payment.

For a vulnerability, contact the repository maintainer privately through the
repository's security channel when configured. Do not file real personal data,
malware payloads or live credentials in a public issue.
