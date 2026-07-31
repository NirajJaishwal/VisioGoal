"""Football Intelligence Platform backend package.

This runs before any submodule (and before FastAPI is imported by `app.main`),
so it is the right place to silence one upstream-only deprecation: FastAPI /
Starlette 1.3 access the deprecated ``HTTP_422_UNPROCESSABLE_ENTITY`` constant at
import time from inside their own machinery. Our code already uses the new name
(``HTTP_422_UNPROCESSABLE_CONTENT``), so this warning is not actionable here.
"""

import warnings

from starlette.exceptions import StarletteDeprecationWarning

warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
