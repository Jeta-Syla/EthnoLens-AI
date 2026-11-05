"""EthnoLens data pipeline.

HTTPS requests use the operating system's certificate store, so they also work behind
antivirus or network TLS inspection (for example Avast on Windows). Verification stays on.
"""

import truststore

truststore.inject_into_ssl()
