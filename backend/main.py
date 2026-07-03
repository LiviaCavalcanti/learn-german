"""Dev launcher for the Sprachheft backend."""

from __future__ import annotations

import uvicorn

from sprachheft.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "sprachheft.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
