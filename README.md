<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Intelligence Service</title>
</head>
<body>

<h1>Document Intelligence &amp; Question Extraction Service</h1>

<p>
    A FastAPI-based backend service for uploading PDF/image documents,
    processing them asynchronously, extracting questions and options,
    associating answer keys, and exposing structured results through REST APIs.
</p>

<h2>Features</h2>

<ul>
    <li>FastAPI REST API</li>
    <li>JWT-based authentication</li>
    <li>Argon2 password hashing</li>
    <li>PostgreSQL persistence</li>
    <li>SQLAlchemy 2.x ORM</li>
    <li>Alembic database migrations</li>
    <li>Celery + Redis asynchronous processing</li>
    <li>PDF extraction using PyMuPDF</li>
    <li>OCR using Tesseract</li>
    <li>OpenCV image preprocessing</li>
    <li>Question and option extraction</li>
    <li>Multi-page question handling</li>
    <li>Source-page tracking</li>
    <li>Answer-key detection and association</li>
    <li>Confidence and review flags</li>
    <li>File validation and 10 MB upload limit</li>
    <li>Swagger/OpenAPI documentation</li>
    <li>Automated testing with pytest</li>
</ul>

<h2>Architecture</h2>

<pre>
Client
  |
  v
FastAPI API
  |
  +------------------+
  |        |         |
  v        v         v
PostgreSQL Redis   Storage
             |
             v
           Celery
             |
             v
      Document Worker
             |
       +-----+-----+
       |     |     |
      PDF   OCR  Extraction
       |     |     |
       +-----+-----+
             |
             v
    Question Extraction
             |
             v
     Answer Association
             |
             v
     Confidence / Review
</pre>

<h2>Technology Stack</h2>

<table>
    <thead>
        <tr>
            <th>Component</th>
            <th>Technology</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>API</td>
            <td>FastAPI</td>
        </tr>
        <tr>
            <td>Language</td>
            <td>Python 3.12</td>
        </tr>
        <tr>
            <td>Database</td>
            <td>PostgreSQL 16</td>
        </tr>
        <tr>
            <td>ORM</td>
            <td>SQLAlchemy 2.x</td>
        </tr>
        <tr>
            <td>Migrations</td>
            <td>Alembic</td>
        </tr>
        <tr>
            <td>Authentication</td>
            <td>JWT + Argon2</td>
        </tr>
        <tr>
            <td>Queue</td>
            <td>Celery</td>
        </tr>
        <tr>
            <td>Broker</td>
            <td>Redis</td>
        </tr>
        <tr>
            <td>PDF Processing</td>
            <td>PyMuPDF</td>
        </tr>
        <tr>
            <td>OCR</td>
            <td>Tesseract + pytesseract</td>
        </tr>
        <tr>
            <td>Image Processing</td>
            <td>OpenCV + Pillow</td>
        </tr>
        <tr>
            <td>Testing</td>
            <td>pytest + HTTPX</td>
        </tr>
        <tr>
            <td>Containerization</td>
            <td>Docker / Docker Compose</td>
        </tr>
    </tbody>
</table>

<h2>Installation</h2>

<h3>Clone Repository</h3>

<pre>
git clone https://github.com/Md-Mohseen-Ali/document-intelligence-service.git
cd document-intelligence-service
</pre>

<h3>Create Virtual Environment</h3>

<pre>
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
</pre>

<h3>Install Dependencies</h3>

<pre>
pip install -r requirements.txt
</pre>

<h2>Environment Configuration</h2>

<pre>
APP_NAME=Document Intelligence Service
APP_VERSION=1.0.0
DEBUG=true

DATABASE_URL=postgresql+psycopg://app_user:app_password@localhost:5432/document_intelligence

JWT_SECRET=replace-with-a-secure-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
</pre>

<p><strong>Never commit real secrets or production credentials.</strong></p>

<h2>Start PostgreSQL and Redis</h2>

<pre>
docker compose up -d
</pre>

<h2>Run Database Migration</h2>

<pre>
alembic upgrade head
</pre>

<h2>Run FastAPI</h2>

<pre>
uvicorn app.main:app --reload
</pre>

<p>API: <code>http://127.0.0.1:8000</code></p>

<p>Swagger: <code>http://127.0.0.1:8000/docs</code></p>

<p>Health: <code>http://127.0.0.1:8000/health</code></p>

<h2>Run Celery Worker</h2>

<pre>
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
</pre>

<h2>API Endpoints</h2>

<h3>Authentication</h3>

<pre>
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
</pre>

<h3>Documents</h3>

<pre>
POST /api/v1/documents
GET  /api/v1/documents/{document_id}/status
</pre>

<h3>Questions</h3>

<pre>
GET /api/v1/documents/{document_id}/questions
GET /api/v1/questions/{question_id}
</pre>

<h3>Answers</h3>

<pre>
GET /api/v1/questions/{question_id}/answer
</pre>

<h2>Processing Flow</h2>

<pre>
Upload Document
      |
      v
Validate File
      |
      v
Store Document
      |
      v
Create Processing Job
      |
      v
Queue Celery Task
      |
      v
Document Worker
      |
      +----------------------+
      |                      |
      v                      v
Digital PDF              Scanned PDF
      |                      |
      v                      v
PyMuPDF                  PDF Rendering
Text Extraction               |
                             v
                         OpenCV + OCR
                             |
                             v
                       Tesseract OCR
      |                      |
      +----------+-----------+
                 |
                 v
        Question Extraction
                 |
                 v
          Option Extraction
                 |
                 v
        Source Page Mapping
                 |
                 v
       Confidence / Review
                 |
                 v
            PostgreSQL
</pre>

<h2>OCR Processing</h2>

<p>
Scanned PDF pages are rendered and processed using OpenCV and Tesseract OCR.
OCR confidence is retained for review purposes.
</p>

<pre>
Document
   |
   v
Render Page
   |
   v
OpenCV Preprocessing
   |
   v
Tesseract OCR
   |
   v
Extracted Text
   |
   v
Question Parser
</pre>

<h2>Question Extraction</h2>

<p>Supported question formats include:</p>

<pre>
1. What is Java?

2) Which protocol is used for...?

Question 3. Explain...

Q4. What does REST stand for?
</pre>

<p>Supported option formats include:</p>

<pre>
A. Option one
B. Option two
C. Option three
D. Option four
</pre>

<pre>
A) Option one
B) Option two
C) Option three
D) Option four
</pre>

<p>
The extraction pipeline also supports questions that continue across multiple pages.
</p>

<h2>Answer Key Processing</h2>

<p>The service supports separate answer-key documents.</p>

<pre>
Answer Key

1. A
2. C
3. B
4. A
5. A
6. C
7. D
</pre>

<p>Supported variations include:</p>

<pre>
1-A
2-C
Question 3. B
Q4. D
</pre>

<p>
Answers are matched to questions using normalized question numbers.
</p>

<h2>Confidence and Review</h2>

<p>
The system stores confidence information for OCR pages and extracted questions.
Results marked for review can be verified by a human.
</p>

<h2>Security</h2>

<ul>
    <li>JWT authentication</li>
    <li>Argon2 password hashing</li>
    <li>Protected API endpoints</li>
    <li>User ownership checks</li>
    <li>File extension validation</li>
    <li>MIME/content-type validation</li>
    <li>10 MB maximum upload size</li>
    <li>Environment-based configuration</li>
    <li>Secrets excluded from source control</li>
</ul>

<h2>Testing</h2>

<pre>
pytest -q
</pre>

<p>Tests cover:</p>

<ul>
    <li>Authentication</li>
    <li>JWT security</li>
    <li>Password hashing</li>
    <li>Question parsing</li>
    <li>Question extraction</li>
    <li>OCR/scanned document processing</li>
    <li>Answer-key parsing</li>
    <li>Answer association</li>
</ul>

<h2>Storage</h2>

<p>
The MVP uses a local storage abstraction for uploaded documents.
The abstraction allows production object storage such as MinIO or S3
to be introduced later.
</p>

<h2>Scalability</h2>

<pre>
              FastAPI
                 |
               Redis
                 |
        +--------+--------+
        |        |        |
     Worker   Worker   Worker
</pre>

<p>
Additional Celery workers can process documents concurrently as workload increases.
</p>

<h2>Design Tradeoffs</h2>

<h3>Local Storage</h3>

<p>
Local storage was selected for the assignment MVP to keep setup simple.
Production deployment can replace it with MinIO or S3.
</p>

<h3>OCR</h3>

<p>
Tesseract was selected because it can run locally without requiring
an external paid OCR API.
</p>

<h3>Deterministic Question Parsing</h3>

<p>
The initial extraction layer combines OCR with deterministic parsing,
making the extraction behavior easier to test and explain.
</p>

<h3>Asynchronous Processing</h3>

<p>
Document processing is moved to Celery workers so API requests do not
block during OCR and extraction.
</p>

<h2>Future Improvements</h2>

<ul>
    <li>MinIO/S3 object storage</li>
    <li>Better rotation detection</li>
    <li>Advanced layout-aware extraction</li>
    <li>Improved image/table extraction</li>
    <li>Explicit related-document relationships</li>
    <li>Human review/update workflow</li>
    <li>Advanced confidence aggregation</li>
    <li>Better malformed-document handling</li>
    <li>Horizontal worker scaling</li>
    <li>Production monitoring and metrics</li>
</ul>

<h2>Related Frontend</h2>

<p>
<a href="https://github.com/Md-Mohseen-Ali/document-intelligence-frontend">
Document Intelligence Frontend
</a>
</p>

<h2>License</h2>

<p>
Developed as an engineering assignment and demonstration project.
</p>

</body>
</html>
