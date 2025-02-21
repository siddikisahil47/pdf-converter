# PDF Converter Tool

A powerful PDF conversion tool built with Python, similar to iLovePDF.com. This tool provides various PDF manipulation features through a user-friendly web interface.

## Features

- PDF to Image conversion
- Image to PDF conversion
- PDF merging
- PDF splitting
- PDF compression
- PDF to Word conversion
- Word to PDF conversion

## Setup Instructions

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the Streamlit frontend:

```bash
streamlit run src/frontend/app.py
```

3. Run the FastAPI backend (in a separate terminal):

```bash
uvicorn src.backend.main:app --reload
```

## Project Structure

```
pdf-converter/
├── src/
│   ├── backend/
│   │   ├── main.py
│   │   └── utils/
│   │       └── pdf_operations.py
│   └── frontend/
│       └── app.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+
- All dependencies listed in requirements.txt

## License

MIT License
