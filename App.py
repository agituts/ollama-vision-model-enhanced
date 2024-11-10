import streamlit as st
import ollama
from PIL import Image
import io
import json
from datetime import datetime, timedelta
import os
import shutil

def delete_conversation(filename):
    json_path = os.path.join('conversations', filename)
    if os.path.exists(json_path):
        os.remove(json_path)
    
    # Extract timestamp from filename
    base_filename = os.path.basename(filename)
    timestamp = base_filename.replace('conversation_', '').replace('.json', '')
    # Delete associated image files
    image_extensions = ['png', 'jpg', 'jpeg']
    for ext in image_extensions:
        image_filename = f'image_{timestamp}.{ext}'
        image_path = os.path.join('conversations', image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Also delete current_conversation.json if it matches
    if os.path.exists('conversations/current_conversation.json'):
        with open('conversations/current_conversation.json', 'r') as f:
            current_data = json.load(f)
            if current_data.get('timestamp') == timestamp:
                os.remove('conversations/current_conversation.json')

def save_conversation(messages, context, image=None, filename=None, title=None):
    if not messages:
        return None
        
    if not os.path.exists('conversations'):
        os.makedirs('conversations')
    
    # Generate a new timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = os.path.join('conversations', f'conversation_{timestamp}.json')
    
    # Generate a default title using the first user message or timestamp
    first_user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
    default_title = first_user_message if first_user_message else f"Conversation on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Use the provided title or default title
    conversation_title = title or default_title

    conversation_data = {
        'timestamp': timestamp,
        'messages': messages,
        'context': context,
        'title': conversation_title
    }
    
    # Save the conversation JSON
    with open(new_filename, 'w') as f:
        json.dump(conversation_data, f, indent=4)
    
    # Also save as 'current_conversation.json' for auto-recovery
    with open('conversations/current_conversation.json', 'w') as f:
        json.dump(conversation_data, f, indent=4)
    
    if image:
        # Get image format extension
        image_format = image.format.lower() if image.format else 'png'
        ext = 'jpg' if image_format == 'jpeg' else image_format
        image_filename = f'image_{timestamp}.{ext}'
        image.save(os.path.join('conversations', image_filename))
    
    # If updating an existing conversation, delete the old files
    if filename and os.path.exists(filename):
        delete_conversation(os.path.basename(filename))
    
    return new_filename

def load_conversation(filename):
    # Load conversation data
    with open(filename, 'r') as f:
        conv_data = json.load(f)
    
    # Extract timestamp from filename
    base_filename = os.path.basename(filename)
    timestamp = base_filename.replace('conversation_', '').replace('.json', '')
    
    # Update the timestamp in conv_data to match the filename
    conv_data['timestamp'] = timestamp
    
    # Try to load associated image
    image_extensions = ['png', 'jpg', 'jpeg']
    image = None
    for ext in image_extensions:
        image_filename = f'image_{timestamp}.{ext}'
        image_path = os.path.join('conversations', image_filename)
        if os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                break  # Exit loop if image is found
            except Exception as e:
                print(f"Error loading image {image_filename}: {e}")
    return conv_data, image

def get_saved_conversations():
    if not os.path.exists('conversations'):
        return {}
    files = [f for f in os.listdir('conversations') if f.startswith('conversation_') and f.endswith('.json')]
    conversations = []
    for file in files:
        with open(os.path.join('conversations', file), 'r') as f:
            data = json.load(f)
            # Extract timestamp from filename
            timestamp_str = file.replace('conversation_', '').replace('.json', '')
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            conversations.append({
                'filename': file,
                'timestamp': timestamp,
                'title': data.get('title', f"Conversation on {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"),
                'preview': data['messages'][0]['content'] if data['messages'] else 'Empty conversation'
            })
    # Now categorize conversations by date ranges
    categorized_conversations = {}
    now = datetime.now()
    today = now.date()
    yesterday = (now - timedelta(days=1)).date()
    last_week = (now - timedelta(days=7)).date()
    last_month = (now - timedelta(days=30)).date()
    for conv in conversations:
        conv_date = conv['timestamp'].date()
        if conv_date == today:
            key = 'Today'
        elif conv_date == yesterday:
            key = 'Yesterday'
        elif conv_date >= last_week:
            key = 'Last 7 Days'
        elif conv_date >= last_month:
            key = 'Last 30 Days'
        else:
            key = 'Older'
        if key not in categorized_conversations:
            categorized_conversations[key] = []
        categorized_conversations[key].append(conv)
    return categorized_conversations

def process_image_and_text(image, text_prompt, messages_history, context):
    if image is not None:
        img_byte_arr = io.BytesIO()
        # Ensure the image format is set
        image_format = image.format if image.format else 'PNG'
        image.save(img_byte_arr, format=image_format)
        img_byte_arr = img_byte_arr.getvalue()
        
        system_prompt = {
            "role": "system",
            "content": """You are an AI assistant that provides accurate image analysis. 
            Follow these guidelines:
            1. Only make statements that you can verify from the image
            2. If you are unsure about something, explicitly state your uncertainty
            3. Consider the provided context for better understanding
            4. Maintain consistency with previous responses
            5. Focus on factual observations rather than assumptions"""
        }
        
        max_history = 5
        recent_messages = messages_history[-max_history:] if len(messages_history) > max_history else messages_history
        
        contextualized_prompt = (
            f"Context: {context}\nQuestion: {text_prompt}" 
            if context 
            else text_prompt
        )
        
        try:
            response = ollama.chat(
                model='llama3.2-vision',
                messages=[
                    system_prompt,
                    *recent_messages,
                    {
                        'role': 'user',
                        'content': contextualized_prompt,
                        'images': [img_byte_arr]
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error processing request: {str(e)}"
    return "Please upload an image first"

def clear_image_state():
    st.session_state.current_image = None
    st.session_state.uploaded_file = None
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = 0
    st.session_state.file_uploader_key += 1

def clear_all_state():
    st.session_state.messages = []
    st.session_state.context = ""
    st.session_state.title = ""  # Reset the title
    st.session_state.is_loading_conversation = False
    st.session_state.current_conversation_filename = None
    clear_image_state()
    # Remove current_conversation.json
    if os.path.exists('conversations/current_conversation.json'):
        os.remove('conversations/current_conversation.json')

def main():
    st.set_page_config(
        page_title="Enhanced Image Analysis with Ollama",
        page_icon="🔍",
        layout="wide"
    )

    # Inject custom CSS styles
    st.markdown("""
    <style>
    .sidebar-content button {
        font-size: 16px !important;
        padding: 2px 6px !important;
    }
    .conversation-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .conversation-icons {
        display: flex;
        justify-content: center;
        gap: 10px;
    }
    .conversation-icons button {
        font-size: 16px !important;
        padding: 4px 8px !important;
    }
    .conversation-item {
        padding: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    .conversation-item:last-child {
        border-bottom: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize all session state variables before use
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'context' not in st.session_state:
        st.session_state.context = ""
    if 'title' not in st.session_state:
        st.session_state.title = ''  # Initialize title
    if 'is_loading_conversation' not in st.session_state:
        st.session_state.is_loading_conversation = False
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = 0
    if 'current_conversation_filename' not in st.session_state:
        st.session_state.current_conversation_filename = None
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = False
    if 'delete_target' not in st.session_state:
        st.session_state.delete_target = ''
    if 'delete_all_confirm' not in st.session_state:
        st.session_state.delete_all_confirm = False
    if 'load_conversation_filename' not in st.session_state:
        st.session_state.load_conversation_filename = None
    if 'edit_title_mode' not in st.session_state:
        st.session_state.edit_title_mode = False
    if 'edit_title_target' not in st.session_state:
        st.session_state.edit_title_target = ''
    if 'new_title' not in st.session_state:
        st.session_state.new_title = ''

    # Attempt to load current conversation if it exists
    if os.path.exists('conversations/current_conversation.json') and not st.session_state.messages:
        # Load the conversation data
        with open('conversations/current_conversation.json', 'r') as f:
            conversation_data = json.load(f)
            # Update the timestamp in conversation_data to match the filename
            timestamp = conversation_data.get('timestamp', '')
            st.session_state.messages = conversation_data.get('messages', [])
            st.session_state.context = conversation_data.get('context', '')
            st.session_state.title = conversation_data.get('title', '')  # Load title
            st.session_state.is_loading_conversation = False
            st.session_state.current_conversation_filename = os.path.join(
                'conversations', f"conversation_{timestamp}.json"
            )
            # Load the image if any
            image = None
            image_extensions = ['png', 'jpg', 'jpeg']
            for ext in image_extensions:
                image_filename = f'image_{timestamp}.{ext}'
                image_path = os.path.join('conversations', image_filename)
                if os.path.exists(image_path):
                    try:
                        image = Image.open(image_path)
                        break  # Exit loop if image is found
                    except Exception as e:
                        print(f"Error loading image {image_filename}: {e}")
            if image:
                st.session_state.current_image = image
                st.session_state.uploaded_file = None
            else:
                clear_image_state()

    st.title("Enhanced Image Analysis with Ollama Vision Model")

    # Collapsible sidebar for conversation management
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        with st.expander("Conversation Management", expanded=False):
            st.subheader("Context Management")
            st.session_state.context = st.text_area(
                "Add context for the conversation",
                st.session_state.context,
                help="Add any relevant context that should be considered during the analysis"
            )
            
            if st.button("New Conversation"):
                if st.session_state.messages and not st.session_state.is_loading_conversation:
                    # Save the conversation with a new timestamp
                    st.session_state.current_conversation_filename = save_conversation(
                        st.session_state.messages,
                        st.session_state.context,
                        st.session_state.current_image,
                        st.session_state.current_conversation_filename,
                        title=st.session_state.title  # Pass the title
                    )
                clear_all_state()
                st.rerun()
            
            st.subheader("Previous Conversations")
            conversations = get_saved_conversations()
            for category in ['Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days', 'Older']:
                if category in conversations:
                    st.markdown(f"### {category}")
                    for conv in conversations[category]:
                        timestamp_str = conv['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

                        # Create a container for each conversation item
                        with st.container():
                            st.markdown(f"<div class='conversation-item'>", unsafe_allow_html=True)

                            # Display the conversation title
                            st.markdown(f"<div class='conversation-title'>{conv['title']}</div>", unsafe_allow_html=True)

                            # Handle edit title mode
                            if st.session_state.edit_title_mode and st.session_state.edit_title_target == conv['filename']:
                                st.session_state.new_title = st.text_input(
                                    "Edit Title",
                                    value=st.session_state.new_title,
                                    key=f"edit_title_{conv['filename']}"
                                )
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 Save", key=f"save_title_{conv['filename']}"):
                                        # Save the new title
                                        conv_data, _ = load_conversation(os.path.join('conversations', conv['filename']))
                                        conv_data['title'] = st.session_state.new_title
                                        with open(os.path.join('conversations', conv['filename']), 'w') as f:
                                            json.dump(conv_data, f, indent=4)
                                        # Update the title in session state if this is the current conversation
                                        if st.session_state.current_conversation_filename == os.path.join('conversations', conv['filename']):
                                            st.session_state.title = st.session_state.new_title  # Update the title
                                        st.session_state.edit_title_mode = False
                                        st.session_state.edit_title_target = ''
                                        st.session_state.new_title = ''
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ Cancel", key=f"cancel_edit_{conv['filename']}"):
                                        st.session_state.edit_title_mode = False
                                        st.session_state.edit_title_target = ''
                                        st.session_state.new_title = ''
                                        st.rerun()
                            else:
                                # Display the action icons centered below the title
                                st.markdown("<div class='conversation-icons'>", unsafe_allow_html=True)
                                # Center the icons using columns
                                col_icon1, col_icon2, col_icon3 = st.columns([1, 1, 1])
                                with col_icon1:
                                    if st.button("📂", key=f"load_{conv['filename']}", help="Load Conversation"):
                                        st.session_state.load_conversation_filename = conv['filename']
                                        st.rerun()
                                with col_icon2:
                                    if st.button("✏️", key=f"edit_title_btn_{conv['filename']}", help="Edit Title"):
                                        st.session_state.edit_title_mode = True
                                        st.session_state.edit_title_target = conv['filename']
                                        st.session_state.new_title = conv['title']
                                        st.rerun()
                                with col_icon3:
                                    if st.button("🗑️", key=f"delete_{conv['filename']}", help="Delete Conversation"):
                                        st.session_state.delete_confirm = True
                                        st.session_state.delete_target = conv['filename']
                                        st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)

                            # Display the delete confirmation dialog
                            if st.session_state.delete_confirm and st.session_state.delete_target == conv['filename']:
                                st.error(f"⚠️ Confirm delete **\"{conv['title']}\"**?")
                                col_confirm, col_cancel = st.columns(2)
                                with col_confirm:
                                    if st.button("✅ Yes", key=f"confirm_delete_{conv['filename']}"):
                                        delete_conversation(st.session_state.delete_target)
                                        st.session_state.delete_confirm = False
                                        st.session_state.delete_target = ''
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ No", key=f"cancel_delete_{conv['filename']}"):
                                        st.session_state.delete_confirm = False
                                        st.session_state.delete_target = ''
                                        st.rerun()

                            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.load_conversation_filename:
                # Load the conversation
                filename = st.session_state.load_conversation_filename
                loaded_conv, loaded_image = load_conversation(os.path.join('conversations', filename))
                st.session_state.messages = loaded_conv['messages']
                st.session_state.context = loaded_conv.get('context', '')
                st.session_state.title = loaded_conv.get('title', '')  # Store the title
                st.session_state.is_loading_conversation = True
                if loaded_image:
                    st.session_state.current_image = loaded_image
                    st.session_state.uploaded_file = None
                    # Reset file uploader key to reload the widget
                    st.session_state.file_uploader_key += 1
                else:
                    clear_image_state()
                # Set current conversation filename
                st.session_state.current_conversation_filename = os.path.join('conversations', filename)
                # Clear the load_conversation_filename after loading
                st.session_state.load_conversation_filename = None
                st.rerun()

            if st.button("Delete All Conversations"):
                st.session_state.delete_all_confirm = True
                st.rerun()

            # Confirmation for deleting all conversations
            if st.session_state.delete_all_confirm:
                st.error("⚠️ Are you sure you want to delete ALL conversations? This action cannot be undone.")
                col_confirm_all, col_cancel_all = st.columns([1, 1])
                with col_confirm_all:
                    if st.button("Yes, Delete All", key="confirm_delete_all"):
                        if os.path.exists('conversations'):
                            shutil.rmtree('conversations')
                        st.session_state.delete_all_confirm = False
                        # Also clear session state
                        clear_all_state()
                        st.rerun()
                with col_cancel_all:
                    if st.button("Cancel", key="cancel_delete_all"):
                        st.session_state.delete_all_confirm = False
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=['png', 'jpg', 'jpeg'],
            key=f"file_uploader_{st.session_state.file_uploader_key}"
        )
        
        # Display either uploaded image or loaded image
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            # Ensure the image format is set
            if not image.format:
                image_format = uploaded_file.type.split('/')[-1].upper()
                image.format = image_format
            st.session_state.current_image = image
            st.image(image, caption='Uploaded Image', use_container_width=True)
        elif st.session_state.current_image is not None:
            st.image(st.session_state.current_image, caption='Loaded Image', use_container_width=True)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Enter your prompt here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        if st.session_state.current_image is not None:
            with st.spinner('Processing...'):
                messages_history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]
                response = process_image_and_text(
                    st.session_state.current_image,
                    prompt,
                    messages_history,
                    st.session_state.context
                )
                
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Reset is_loading_conversation after new messages are added
                st.session_state.is_loading_conversation = False
                
                # Auto-save the conversation with new timestamp
                st.session_state.current_conversation_filename = save_conversation(
                    st.session_state.messages,
                    st.session_state.context,
                    st.session_state.current_image,
                    st.session_state.current_conversation_filename,
                    title=st.session_state.title  # Pass the stored title
                )
        else:
            st.error("Please upload an image")

if __name__ == "__main__":
    main()