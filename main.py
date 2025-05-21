import streamlit as st
import os
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup # Import BeautifulSoup
from doc_utils import extract_title_from_pdf, extract_title_from_docx, search_text_in_file, highlight_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
from collections import Counter # Import Counter
from urllib.parse import urljoin
from dropbox_utils import get_dropbox_client, create_folder, upload_file_to_dropbox, list_dropbox_files

# Configuration
DOC_FOLDER = 'sample_documents'
DROPBOX_FOLDER_NAME = 'Cloud Document Analytics'
os.makedirs(DOC_FOLDER, exist_ok=True)

# Initialize session state for performance metrics and Dropbox client
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        'upload_time': [],
        'search_time': [],
        'sort_time': [],
        'classify_time': []
    }

if 'dropbox_client' not in st.session_state:
    st.session_state.dropbox_client = None

# Initialize session state for tracking uploaded files to Dropbox
if 'uploaded_files_dropbox' not in st.session_state:
    st.session_state.uploaded_files_dropbox = set()

st.title("📄 Cloud Document Analytics")

# Dropbox Authentication Section
st.header("🔐 Dropbox Authentication")
dropbox_token = st.text_input("Enter your Dropbox Access Token:", type="password")
if dropbox_token and not st.session_state.dropbox_client:
    try:
        st.session_state.dropbox_client = get_dropbox_client(dropbox_token)
        st.success("✅ Successfully connected to Dropbox!")
    except Exception as e:
        st.error(f"❌ Failed to connect to Dropbox: {str(e)}")
        st.session_state.dropbox_client = None

# Document Upload Section
st.header("📤 Document Upload")
uploaded_files = st.file_uploader("Upload PDF or Word files", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    start_time = time.time()
    
    # Create Dropbox folder if connected
    dropbox_folder_path = None
    if st.session_state.dropbox_client:
        try:
            dropbox_folder_path = create_folder(st.session_state.dropbox_client, DROPBOX_FOLDER_NAME)
            st.success(f"✅ Created Dropbox folder: {DROPBOX_FOLDER_NAME}")
        except Exception as e:
            st.warning(f"⚠️ Dropbox folder creation failed: {e}")
    
    for file in uploaded_files:
        # Check if the file has already been uploaded to Dropbox in this session
        if file.name in st.session_state.uploaded_files_dropbox:
            st.info(f"ℹ️ File {file.name} already uploaded to Dropbox in this session.")
            continue # Skip processing and uploading this file again

        file_path = os.path.join(DOC_FOLDER, file.name)
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        # Upload to Dropbox if connected
        if st.session_state.dropbox_client and dropbox_folder_path:
            try:
                dropbox_path = upload_file_to_dropbox(st.session_state.dropbox_client, file_path, dropbox_folder_path)
                st.success(f"✅ Uploaded {file.name} to Dropbox")
                # Add filename to session state to track that it's uploaded
                st.session_state.uploaded_files_dropbox.add(file.name)
            except Exception as e:
                st.warning(f"⚠️ Dropbox upload failed for {file.name}: {e}")
        else:
             # If not connected to Dropbox, still process and save locally
             st.success(f"✅ Saved {file.name} locally.")
             # Add filename to session state if only saving locally (optional, depending on desired behavior)
             # If you only want to track Dropbox uploads, remove the line below
             st.session_state.uploaded_files_dropbox.add(file.name) # Still mark as processed for this session

    upload_time = time.time() - start_time
    st.session_state.metrics['upload_time'].append(upload_time)
    st.success(f"✅ File processing complete! (Time: {upload_time:.2f}s)")

# Fetch Document from Web Section
st.header("📥 Fetch Document from Web")
fetch_option = st.radio("Select fetch option:", ["Direct File URL", "Web Page URL to scrape links"])
url_input = st.text_input("Enter URL:")

if st.button("Fetch Document(s)"):
    if url_input:
        if fetch_option == "Direct File URL":
            # Existing logic for direct file URL
            try:
                response = requests.get(url_input, stream=True)
                response.raise_for_status() # Raise an exception for bad status codes

                # Determine file name and type from URL or headers
                filename = os.path.basename(url_input)
                content_type = response.headers.get('content-type', '')

                if 'pdf' in content_type.lower() or filename.lower().endswith('.pdf'):
                    file_extension = '.pdf'
                elif 'wordprocessingml.document' in content_type.lower() or filename.lower().endswith('.docx'):
                     file_extension = '.docx'
                else:
                    st.warning(f"⚠️ Unsupported file type from URL: {url_input}")
                    st.info(f"Detected Content-Type: {content_type}, Filename: {filename}")
                    filename = None # Indicate unsupported type

                if filename:
                    # Ensure filename is unique to avoid overwriting existing files
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(os.path.join(DOC_FOLDER, filename)):
                        filename = f"{base}_{counter}{ext}"
                        counter += 1

                    file_path = os.path.join(DOC_FOLDER, filename)
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    st.success(f"✅ Fetched and added {filename} from web!")

                    # Note: You would ideally upload to Dropbox here if enabled

                
            except requests.exceptions.RequestException as e:
                st.warning(f"⚠️ Failed to fetch document from {url_input}: {e}")
            except Exception as e:
                st.warning(f"⚠️ An error occurred while processing {url_input}: {e}")
        
        elif fetch_option == "Web Page URL to scrape links":
            # New logic for scraping links from a web page
            if url_input:
                st.write(f"Attempting to scrape links from: {url_input}")
                try:
                    # Fetch the webpage
                    response = requests.get(url_input)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all links
                    links = soup.find_all('a')
                    doc_links = []
                    
                    # Look for document links
                    for link in links:
                        href = link.get('href', '')
                        # Check for direct document links
                        if any(href.lower().endswith(ext) for ext in ['.pdf', '.docx', '.doc', '.txt', '.rtf']):
                            doc_links.append(href)
                        # Check for arXiv links - improved pattern matching
                        elif 'arxiv.org/abs/' in href:
                            # Extract the paper ID
                            paper_id = href.split('/')[-1]
                            # Create direct PDF link
                            pdf_link = f'https://arxiv.org/pdf/{paper_id}.pdf'
                            doc_links.append(pdf_link)
                    
                    if doc_links:
                        st.write(f"Found {len(doc_links)} document links")
                        for link in doc_links:
                            # Handle relative URLs
                            if not link.startswith(('http://', 'https://')):
                                link = urljoin(url_input, link)
                            
                            try:
                                # Download the document with headers to mimic a browser
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                    'Accept-Language': 'en-US,en;q=0.9',
                                    'Referer': url_input # Add referer header
                                }
                                response = requests.get(link, headers=headers, timeout=30)
                                response.raise_for_status()
                                
                                # Get filename from URL or use a default
                                filename = os.path.basename(link)
                                if not filename:
                                    filename = f"document_{len(doc_links)}.pdf"
                                
                                # Save the document
                                file_path = os.path.join(DOC_FOLDER, filename)
                                with open(file_path, 'wb') as f:
                                    f.write(response.content)
                                
                                st.success(f"Downloaded: {filename}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Failed to download {link}: {str(e)}")
                            except Exception as e:
                                st.error(f"Error processing {link}: {str(e)}")
                    else:
                        st.warning("No document links found on this page")
                except Exception as e:
                    st.error(f"Error scraping the webpage: {str(e)}")

    else:
        st.info("Please enter a URL.")

# Document Sorting Section
st.header("📑 Document Sorting")
if st.button("Sort Documents by Title"):
    start_time = time.time()
    
    titles = []
    for filename in os.listdir(DOC_FOLDER):
        path = os.path.join(DOC_FOLDER, filename)
        if filename.endswith('.pdf'):
            title = extract_title_from_pdf(path)
        elif filename.endswith('.docx'):
            title = extract_title_from_docx(path)
        else:
            continue
        titles.append((filename, title))
    
    sorted_titles = sorted(titles, key=lambda x: x[1])
    
    sort_time = time.time() - start_time
    st.session_state.metrics['sort_time'].append(sort_time)
    
    st.write("### Sorted Files:")
    for name, title in sorted_titles:
        st.write(f"📄 **{name}** → {title}")
    st.info(f"Sorting completed in {sort_time:.2f} seconds")

# Search Section
st.header("🔍 Document Search")
keyword = st.text_input("Search for keyword:")
if keyword:
    start_time = time.time()
    results = []
    
    for filename in os.listdir(DOC_FOLDER):
        path = os.path.join(DOC_FOLDER, filename)
        found, text, matches, search_keyword = search_text_in_file(path, keyword)
        if found:
            results.append((filename, text, search_keyword)) # Pass keyword to results
    
    search_time = time.time() - start_time
    st.session_state.metrics['search_time'].append(search_time)
    
    if results:
        st.write("### Files matching search:")
        for filename, text, search_keyword in results:
            with st.expander(f"✅ {filename}"):
                highlighted_text = highlight_text(text, search_keyword)
                st.markdown(highlighted_text, unsafe_allow_html=True)
    else:
        st.warning("No matches found.")
    
    st.info(f"Search completed in {search_time:.2f} seconds")

# Classification Section
st.header("📊 Document Classification")
if st.button("Classify Documents"):
    start_time = time.time()
    
    # Define categories and their keywords
    categories = {
        'Science': ['research', 'experiment', 'study', 'scientific', 'analysis'],
        'Technology': ['software', 'hardware', 'computer', 'digital', 'system'],
        'Business': ['market', 'finance', 'company', 'business', 'management'],
        'Education': ['learning', 'teaching', 'education', 'student', 'course'],
        'Health': ['medical', 'health', 'treatment', 'patient', 'disease']
    }
    
    texts = []
    names = []
    for filename in os.listdir(DOC_FOLDER):
        path = os.path.join(DOC_FOLDER, filename)
        # For classification, get the full text without specific keyword search
        _, content, _, _ = search_text_in_file(path, ".*") # Use ".*" to get all text, ignore matches/keyword
        texts.append(content)
        names.append(filename)
    
    # Prepare training data
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(texts)
    
    # Create labels based on category keywords
    y = []
    for text in texts:
        scores = {cat: sum(1 for kw in keywords if kw.lower() in text.lower())
                 for cat, keywords in categories.items()}
        # Assign to the category with the highest score, or 'Other' if no keywords match
        if max(scores.values()) > 0:
             y.append(max(scores.items(), key=lambda x: x[1])[0])
        else:
            y.append('Other') # Add 'Other' category for documents without matching keywords

    # Check class counts before splitting
    class_counts = Counter(y)
    can_stratify = all(count >= 2 for count in class_counts.values())

    if len(texts) > 0 and can_stratify:
        # Split data and train model only if stratification is possible
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        model = MultinomialNB()
        model.fit(X_train, y_train)
        # Make predictions on the full dataset for display
        predictions = model.predict(X)

        # Display results
        st.write("### Classification Results:")
        for name, pred in zip(names, predictions):
            st.write(f"📂 {name} → **{pred}**")

        # Show classification metrics - only if test set is not empty
        if len(y_test) > 0:
            st.write("### Classification Metrics:")
            # Filter out categories not present in y_test from the report
            # And handle cases where a class might exist in y_true but not y_pred or vice versa after a very small split
            # Use labels parameter to control which labels are included
            all_labels = list(class_counts.keys())
            predicted_labels = list(set(model.predict(X_test)))
            report_labels = list(set(y_test + predicted_labels))
            st.text(classification_report(y_test, model.predict(X_test), labels=report_labels, zero_division=0))
        else:
             st.info("Not enough diverse documents for detailed classification metrics after splitting.")

        # Save model
        with open("classifier_model.pkl", "wb") as f:
            pickle.dump((vectorizer, model), f)

    elif len(texts) > 0 and not can_stratify:
         st.warning("Not enough documents in one or more categories to train the classifier and show detailed metrics.")
         st.info("Classification shown based on keyword matching.")
         # Display keyword-based classification if full training is skipped
         st.write("### Classification Results (Keyword Match):")
         for name, label in zip(names, y):
             st.write(f"📂 {name} → **{label}**")

    else:
        st.info("No documents available for classification.")


    classify_time = time.time() - start_time
    st.session_state.metrics['classify_time'].append(classify_time)
    st.info(f"Classification completed in {classify_time:.2f} seconds")

# Statistics Section
st.header("📈 Statistics")
if st.checkbox("Show Statistics"):
    total_files = len(os.listdir(DOC_FOLDER))
    total_size = sum(os.path.getsize(os.path.join(DOC_FOLDER, f)) for f in os.listdir(DOC_FOLDER))
    
    st.metric("Number of Documents", total_files)
    st.metric("Total Size (KB)", round(total_size / 1024, 2))
    
    # Performance Metrics
    st.subheader("Performance Metrics")
    metrics_df = pd.DataFrame({
        'Operation': ['Upload', 'Search', 'Sort', 'Classify'],
        'Average Time (s)': [
            sum(st.session_state.metrics['upload_time']) / len(st.session_state.metrics['upload_time']) if st.session_state.metrics['upload_time'] else 0,
            sum(st.session_state.metrics['search_time']) / len(st.session_state.metrics['search_time']) if st.session_state.metrics['search_time'] else 0,
            sum(st.session_state.metrics['sort_time']) / len(st.session_state.metrics['sort_time']) if st.session_state.metrics['sort_time'] else 0,
            sum(st.session_state.metrics['classify_time']) / len(st.session_state.metrics['classify_time']) if st.session_state.metrics['classify_time'] else 0
        ]
    })
    st.dataframe(metrics_df)
