import pandas as pd
import js
from pyodide.ffi import to_js

def download_csv(df, filename="my_data.csv"):
    # 1. Convert the DataFrame to a CSV string in memory
    csv_str = df.to_csv(index=False)
    
    # 2. Package the string into a JavaScript "Blob"
    blob_options = to_js({"type": "text/csv"})
    blob = js.Blob.new([csv_str], blob_options)
    
    # 3. Create a temporary invisible download link
    url = js.URL.createObjectURL(blob)
    link = js.document.createElement("a")
    link.href = url
    link.download = filename
    
    # 4. Add the link to the page, click it programmatically, and remove it
    js.document.body.appendChild(link)
    link.click()
    js.document.body.removeChild(link)
    
    # 5. Clean up the memory
    js.URL.revokeObjectURL(url)