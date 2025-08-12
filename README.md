# gh-smartsheet

Clone and cd into this repo and once in the directory, start a venv.
To start a venv:
```
source venv/bin/activate
pip -r requirements.txt
```

1. To use the script, you must first have both a github token, smartsheet token and smartsheet id.
   Create a .env file in this repository with the variables:
   
   ```
   GITHUB_TOKEN=
   SMARTSHEET_TOKEN=
   SMARTSHEET_SHEET_ID=
   ```

2. Run the script:

    ```
    python3 gh-smartsheet.py
    ```