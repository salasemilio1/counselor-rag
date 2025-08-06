# Memoire - RAG System for Counseling Professionals

Memoire is an intelligent document management and query system designed specifically for counseling and advising professionals. It uses advanced AI techniques to help you organize, search, and extract insights from your session notes and client documents.

## 🎯 What This Application Does

Memoire helps counseling professionals by:

- **Organizing Client Files**: Securely store and manage session notes for each client
- **Intelligent Search**: Ask natural language questions about your clients' progress, patterns, and history
- **Session Preparation**: Get AI-powered insights to help prepare for upcoming sessions
- **Pattern Recognition**: Identify trends and recurring themes across multiple sessions
- **Document Management**: Upload, view, and organize various document types (PDF, Word, Text files)
- **Chat History**: Keep track of your queries and insights for future reference

The system uses Retrieval Augmented Generation (RAG) technology to provide accurate, context-aware responses based on your uploaded documents while keeping all data local and secure.

## 🖥️ System Requirements

### Required Software
Before getting started, you'll need to install:

1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **Node.js 16+** - Download from [nodejs.org](https://nodejs.org)
3. **Ollama** - Download from [ollama.ai](https://ollama.ai)

### Hardware Recommendations
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 5GB+ free space (more if you have many documents)
- **CPU**: Modern multi-core processor (AI processing can be CPU-intensive)

## 📋 Setup Instructions

### Step 1: Install Ollama and Download AI Model

1. Install Ollama following the instructions at [ollama.ai](https://ollama.ai)
2. Open a terminal/command prompt and run:
   ```bash
   ollama pull mistral
   ```
   This downloads the AI model (about 4GB). Wait for it to complete.

3. Start the Ollama server:
   ```bash
   ollama serve
   ```
   Keep this terminal window open - the server must stay running.

### Step 2: Set Up the Backend Server

1. Open a new terminal/command prompt
2. Navigate to the project folder:
   ```bash
   cd path/to/counselor-rag
   ```

3. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```
   
   You should see output like:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```
   Keep this terminal window open.

### Step 3: Set Up the Frontend

1. Open a third terminal/command prompt
2. Navigate to the frontend folder:
   ```bash
   cd path/to/counselor-rag/frontend
   ```

3. Install Node.js dependencies:
   ```bash
   npm install
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   
   You should see output like:
   ```
   Local:   http://localhost:5173/
   ```

5. Open your web browser and go to `http://localhost:5173`

## 🚀 Getting Started

### First Time Setup

1. **Create Your First Client**:
   - Click the "+" button in the sidebar
   - Enter a client name (e.g., "John Smith")
   - The system will automatically create a data folder and client directory

2. **Upload Session Notes**:
   - Select your client from the sidebar
   - Click the upload button (📁) in the top-right
   - Choose your session notes (supports .pdf, .doc, .docx, .txt files)
   - Wait for processing to complete

3. **Start Asking Questions**:
   - Type questions like:
     - "What progress has John made with anxiety management?"
     - "What were the main themes from our last three sessions?"
     - "Has John mentioned any new stressors recently?"

### Understanding the Interface

- **Sidebar**: Lists all your clients with search functionality
- **Chat Area**: Your conversation with the AI about the selected client
- **Document Panel**: View source documents when referenced in AI responses
- **Upload Button**: Add new session notes and documents
- **Settings**: Customize appearance and preferences

## 📁 Data Storage

### Automatic Folder Creation
The system automatically creates a `data` folder structure when you:
- Create your first client
- Upload your first document

The folder structure will look like:
```
data/
├── clients/          # Client-specific documents
│   ├── john/         # Documents for client "john"
│   └── alice/        # Documents for client "alice"
├── chats/           # Saved chat histories
├── metadata/        # System metadata
├── processed/       # Processed document data
└── vector_db/       # AI embeddings database
```

### Data Security
- All data stays on your computer - nothing is sent to external servers
- Client information is stored locally in the `data` folder
- You can backup the entire `data` folder to preserve your information

## 🔧 Troubleshooting

### Common Issues

**Problem**: "Failed to connect to backend"
- **Solution**: Make sure the backend server is running (`python main.py` in the backend folder)

**Problem**: AI responses are very slow or fail
- **Solution**: 
  1. Check that Ollama is running (`ollama serve`)
  2. Verify the mistral model is downloaded (`ollama list`)
  3. Restart the Ollama service if needed

**Problem**: Upload fails or processing takes too long
- **Solution**:
  1. Check file formats (only .pdf, .doc, .docx, .txt supported)
  2. Try smaller files first
  3. Check the backend terminal for error messages

**Problem**: Search doesn't find clients
- **Solution**: Use the search box in the sidebar - type part of the client's name

### Getting Help

If you encounter issues:
1. Check that all three services are running (Ollama, Backend, Frontend)
2. Look for error messages in the terminal windows
3. Try restarting all services in order: Ollama → Backend → Frontend
4. Ensure you have sufficient disk space and RAM available

## 🔒 Privacy & Security

- **Local Processing**: All AI processing happens on your computer
- **No External Calls**: No client data is sent to external AI services
- **Data Control**: You have full control over your data storage and backup
- **Compliance**: Designed with healthcare privacy requirements in mind

## 💡 Tips for Best Results

1. **Consistent Naming**: Use consistent client names across documents
2. **Structured Notes**: Well-organized session notes produce better AI responses
3. **Regular Backups**: Backup your `data` folder regularly
4. **Clear Questions**: Ask specific questions for more targeted responses
5. **Document Organization**: Keep related documents together for each client

## 🛠️ Technical Details

- **Backend**: Python FastAPI server with RAG processing
- **Frontend**: React TypeScript application
- **AI Model**: Local Mistral model via Ollama
- **Database**: ChromaDB for vector embeddings
- **Document Processing**: LangChain for text chunking and processing

---

**Need Support?** This system is designed to be user-friendly, but if you need technical assistance, keep the terminal windows open to see any error messages, and don't hesitate to ask for help from your IT support team.