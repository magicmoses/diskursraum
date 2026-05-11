import os
import uvicorn

port = int(os.environ.get("PORT", 8001))
uvicorn.run("main:app", port=port, host="0.0.0.0", loop="asyncio")
