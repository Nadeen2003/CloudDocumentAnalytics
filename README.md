# Cloud Document Analytics

This project is a simple document management system built using Streamlit. It allows users to upload local documents, fetch documents from web URLs (including scraping links from web pages), perform sorting, searching, and classification on the stored documents, view basic statistics, and optionally upload documents to Dropbox for cloud storage.

## Features

-   **Document Upload:** Upload PDF and Word files directly from your computer. Files are saved locally.
-   **Web Scraping:** Fetch documents directly from a single URL or scrape for PDF/DOCX links on a given webpage. Downloaded files are saved locally.
-   **Dropbox Integration:** Optionally connect to your Dropbox account to automatically upload processed documents for cloud backup.
-   **Document Sorting:** Sort documents based on their extracted titles.
-   **Document Search:** Search for keywords within the document content with highlighting.
-   **Document Classification:** Classify documents into predefined categories using a simple machine learning model.
-   **Statistics:** View basic statistics about the document collection (number of files, total size) and performance metrics for operations.

## Setup

Follow these steps to set up and run the project on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd cloud-document-analytics
    ```

2.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with other Python projects.
    ```bash
    python -m venv venv
    ```
    (Use `python3 -m venv venv` if your system uses `python` for Python 2)

3.  **Activate the Virtual Environment:**
    *   **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    You should see `(venv)` at the beginning of your terminal prompt, indicating the virtual environment is active.

4.  **Install Dependencies:**
    Make sure your virtual environment is activated.
    ```bash
    pip install -r requirements.txt
    ```
    This will install all necessary libraries, including `streamlit`, `pandas`, `numpy`, `scikit-learn`, `PyPDF2`, `python-docx`, `requests`, `beautifulsoup4`, and `dropbox`.

5.  **Set up Dropbox API (Optional but recommended for cloud backup):**
    If you want to use the Dropbox backup feature:
    *   Go to the [Dropbox Developers App Console](https://www.dropbox.com/developers/apps).
    *   Log in to your Dropbox account.
    *   Click "Create app".
    *   Choose "Scoped access".
    *   Select "Full Dropbox".
    *   Give your app a unique name (e.g., "My Document Processor App").
    *   Agree to the terms and click "Create app".
    *   On your app's settings page, go to the **Permissions** tab.
    *   Under "Files and folders", enable the following scopes:
        *   `files.metadata.read`
        *   `files.content.write`
    *   Scroll down and click the "Save" button.
    *   Go back to the **Settings** tab.
    *   Under "OAuth 2", click the "Generate" button to get a new **Generated access token**.
    *   **Copy this token.** You will need to paste it into the running application.

## Running the Application

1.  Ensure your virtual environment is activated (see Setup step 3).
2.  Navigate to the project directory in your terminal.
3.  Run the Streamlit application:
    ```bash
    streamlit run main.py
    ```
4.  Your web browser should open automatically to the application interface (usually at `http://localhost:8501`).

## Usage

Once the application is running:

*   **Dropbox Authentication:** Paste your generated Dropbox Access Token into the input field at the top to connect to your Dropbox account.
*   **Document Upload:** Use the file uploader to select documents from your computer. They will be processed and, if connected, uploaded to your Dropbox in a folder named "Cloud Document Analytics".
*   **Fetch from Web:** Choose the option to fetch from a direct URL or scrape links from a webpage. Enter the URL and click "Fetch Document(s)". Found documents will be downloaded, processed, and potentially uploaded to Dropbox.
*   **Sort Documents:** Click the "Sort Documents by Title" button to see a list of your loaded documents sorted by their titles.
*   **Search Section:** Enter a keyword in the text box and press Enter to search within the loaded documents. Matching documents will be displayed with the keyword highlighted.
*   **Classify Documents:** Click the "Classify Documents" button to run the text classification model on your documents. Results will show the predicted category for each document.
*   **Statistics:** Check the "Show Statistics" box to view the number of documents, total size, and performance timings for operations.

## Project Structure (Simplified)

```
cloud-document-analytics/
├── main.py              # Main Streamlit app logic
├── doc_utils.py         # Document parsing and utility functions
├── dropbox_utils.py     # Dropbox API interactions
├── requirements.txt     # Project dependencies list
└── sample_documents/    # Directory for locally stored documents
```
*(Note: `credentials.json` was for Google Drive and is no longer needed for Dropbox integration)*

## Contributing

If you wish to contribute, please follow a standard GitHub workflow: Fork the repository, create a feature branch, make your changes, and submit a pull request.

## License

This project is open-sourced under the MIT License. See the LICENSE file for more details (if applicable). 