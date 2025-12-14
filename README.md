# backend_service


## Poetry

This project uses poetry. It's a modern dependency management
tool.

To run the project use this set of commands:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```


This will start the server on the configured host, eg: http://localhost:8000.

You can find swagger documentation at `/api/docs`.