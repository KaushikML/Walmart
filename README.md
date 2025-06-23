# SmartChain Prototype

## File Tree
```
.
├── main.py
├── gpt_client.py
├── db.py
├── scheduler.py
├── gradio_app.py
├── requirements.txt
├── .env.sample
└── SmartChain_Blueprint.docx
```

## Running
1. Install Python 3.11+ and create a virtualenv or use Poetry.
2. `pip install -r requirements.txt`
3. Copy `.env.sample` to `.env` and fill in API keys.
4. Initialize the database:
   ```bash
   python -c "from db import Base, engine; import asyncio; asyncio.run(Base.metadata.create_all(engine))"
   ```
5. Start the API:
   ```bash
   uvicorn main:app --reload
   ```
6. Launch the Copilot UI in another terminal:
   ```bash
   python gradio_app.py
   ```
