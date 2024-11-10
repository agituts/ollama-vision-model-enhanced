# Enhanced Image Analysis with Ollama Vision Model

This Streamlit app allows users to analyze images using the Ollama Vision Model, with features such as conversation management.

## Requirements

- Python 3.x
- Streamlit
- Ollama
- Pillow

## Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/amaxkeylogger/ollama-vision-model-enhanced.git
    cd ollama-vision-model-enhanced
    ```

2. **Set Up a Virtual Environmentt (Recommended)**:
   
   Create a virtual environment to isolate project dependencies.

   - On Windows
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
   - On macOS/Linux
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4. **Install Python Dependencies**:

   Install the required Python packages using pip:
   
    ```bash
    pip install -r requirements.txt
    ```
    
    If requirements.txt is missing or incomplete, install the packages manually:

    ```bash
    pip install streamlit ollama Pillow
    ```

5. **Install and Set Up Ollama**:
   
   - Download and Install Ollama: Visit https://ollama.com/ and follow the installation instructions for your operating system.
  
   - Verify Ollama Installation:
   
    ```bash
    ollama version
    ```

6. **Pull the Required Ollama Model**:

   - Pull the llama2:3b-vision model using Ollama:

    ```bash
    ollama pull llama2:3b-vision
    ```

7. **Start the Ollama server**:

   - Start the Ollama server to enable communication with the model:

    ```bash
    ollama serve
    ```
   Tips:
   
   - Keep this terminal window open as the server needs to run continuously. You may open a new terminal window for the next steps.
   - Also, in Windows, you will need to exit any instance of Ollama running in the taskbar.

9. **Launch the App**:

   - In a new terminal window (with your virtual environment activated), navigate to the project directory if you're not already there:
     
   ```bash
    cd ollama-vision-model-enhanced
    ```
   - Launch the app:
     
    ```bash
    streamlit run app.py
    ```
   This command will start the Streamlit server and open the app in your default web browser. If it doesn't open automatically, you can manually visit http://localhost:8501 in your browser.

## Usage

### Basic Operations:
- Upload an Image: Use the file uploader to select and upload an image (PNG, JPG, or JPEG).
- Add Context (Optional): In the sidebar under "Conversation Management", you can add any relevant context for the conversation.
- Enter Prompts: Use the chat input at the bottom of the app to ask questions or provide prompts related to the uploaded image.
- View Responses: The app will display the AI assistant's responses based on the image analysis and your prompts.

### Conversation Management
- Save Conversations: Conversations are saved automatically and can be managed from the sidebar under "Previous Conversations".
- Load Conversations: Load previous conversations by clicking the folder icon (📂) next to the conversation title.
- Edit Titles: Edit conversation titles by clicking the pencil icon (✏️) and saving your changes.
- Delete Conversations: Delete individual conversations using the trash icon (🗑️) or delete all conversations using the "Delete All Conversations" button.

## Troubleshooting

### Issue: Ollama Model Not Found

Symptoms:
- Errors indicating the model cannot be found.
- The app fails to generate responses.
  
Solution:
- Ensure you've pulled the correct model with the exact name used in the code.
- Double-check the model name in the process_image_and_text function:
```python
# Verify model name in code
response = ollama.chat(
    model='llama3.2-vision',   
)
```

### Issue: Connection Error with Ollama Server

Symptoms:
- Errors related to connecting to the Ollama server.
- The app is unable to process image and text prompts.
  
Solution:
- Ensure the Ollama server is running in a terminal (ollama serve).
- Verify there are no firewall restrictions blocking communication.
- Restart the Ollama server if necessary.

### Issue: Missing Python Packages

Symptoms:
- Import errors when running the app (e.g., ModuleNotFoundError).
- The app fails to start due to missing packages.

Solution:
- Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```
- If using a virtual environment, ensure it's activated when installing packages.

### Issue: Streamlit App Not Starting

Symptoms:
- Terminal shows errors when running streamlit run app.py.
- The app doesn't open in the browser.

Solution:
- Verify that you're in the correct directory (ollama-vision-model-enhanced).
- Ensure app.py exists in the directory.
- Check for syntax errors or typos in app.py.

## Additional Tips

Ollama Server:
- The Ollama server needs to run continuously while you're using the app.
- If you close the terminal or the server stops, restart it with:
```bash
ollama serve
```

Running on a Different Port:
- If you need to run the Streamlit app on a different port:
```bash
streamlit run app.py --server.port <PORT_NUMBER>
```

Stopping the App:
- To stop the Streamlit app, press Ctrl+C in the terminal where it's running.
Updating the App Code:
- If you make changes to app.py, Streamlit will prompt you to rerun the app. Click "Rerun" or press R in the terminal.
