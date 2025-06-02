import sys
import pysqlite3
sys.modules['sqlite3'] = pysqlite3
import gradio as gr
import os
import uuid
import json
import datetime
from pathlib import Path
import autogen
import chromadb
import multiprocessing as mp
from autogen.retrieve_utils import TEXT_FORMATS, get_file_from_url, is_url
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import (
    RetrieveUserProxyAgent,
    PROMPT_CODE,
)

TIMEOUT = 60
CHATS_DIR = os.path.join(os.path.dirname(__file__), "chats")
os.makedirs(CHATS_DIR, exist_ok=True)


def initialize_agents(config_list, docs_path=None):
    if isinstance(config_list, gr.State):
        _config_list = config_list.value
    else:
        _config_list = config_list
    if docs_path is None:
        docs_path = "https://raw.githubusercontent.com/microsoft/autogen/main/README.md"

    assistant = RetrieveAssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant.",
    )

    ragproxyagent = RetrieveUserProxyAgent(
        name="ragproxyagent",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        retrieve_config={
            "task": "code",
            "docs_path": docs_path,
            "chunk_token_size": 2000,
            "model": _config_list[0]["model"],
            "client": chromadb.PersistentClient(path="/tmp/chromadb"),
            "embedding_model": "all-mpnet-base-v2",
            "customized_prompt": PROMPT_CODE,
            "get_or_create": True,
            "collection_name": "autogen_rag",
        },
    )

    return assistant, ragproxyagent


def initiate_chat(config_list, problem, queue, n_results=3):
    global assistant, ragproxyagent
    if isinstance(config_list, gr.State):
        _config_list = config_list.value
    else:
        _config_list = config_list
    if len(_config_list[0].get("api_key", "")) < 2:
        queue.put(
            ["Hi, nice to meet you! Please enter your API keys in below text boxs."]
        )
        return
    else:
        llm_config = (
            {
                "request_timeout": TIMEOUT,
                # "seed": 42,
                "config_list": _config_list,
                "use_cache": False,
            },
        )
        assistant.llm_config.update(llm_config[0])
    assistant.reset()
    try:
        ragproxyagent.initiate_chat(
            assistant, problem=problem, silent=False, n_results=n_results
        )
        messages = ragproxyagent.chat_messages
        messages = [messages[k] for k in messages.keys()][0]
        messages = [m["content"] for m in messages if m["role"] == "user"]
        print("messages: ", messages)
    except Exception as e:
        messages = [str(e)]
    queue.put(messages)


def chatbot_reply(input_text):
    """Chat with the agent through terminal."""
    queue = mp.Queue()
    process = mp.Process(
        target=initiate_chat,
        args=(config_list, input_text, queue),
    )
    process.start()
    try:
        # process.join(TIMEOUT+2)
        messages = queue.get(timeout=TIMEOUT)
    except Exception as e:
        messages = [
            str(e)
            if len(str(e)) > 0
            else "Invalid Request to OpenAI, please check your API keys."
        ]
    finally:
        try:
            process.terminate()
        except:
            pass
    return messages


def get_description_text():
    return """
    """


# Chat management functions
def list_chats():
    """List all saved chat sessions"""
    chats = []
    if os.path.exists(CHATS_DIR):
        for filename in os.listdir(CHATS_DIR):
            if filename.endswith('.json'):
                chat_path = os.path.join(CHATS_DIR, filename)
                try:
                    with open(chat_path, 'r') as f:
                        chat_data = json.load(f)
                        chats.append({
                            'id': chat_data.get('id', filename.replace('.json', '')),
                            'title': chat_data.get('title', 'Untitled Chat'),
                            'created_at': chat_data.get('created_at', ''),
                            'last_updated': chat_data.get('last_updated', ''),
                            'messages': chat_data.get('messages', [])
                        })
                except Exception as e:
                    print(f"Error loading chat {filename}: {e}")
    
    # Sort chats by last_updated, newest first
    chats.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
    return chats

def create_new_chat():
    """Create a new chat session"""
    chat_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    new_chat = {
        'id': chat_id,
        'title': f"New Chat {now.split('T')[0]}",
        'created_at': now,
        'last_updated': now,
        'messages': []
    }
    
    # Save to file
    save_chat(new_chat)
    return new_chat

def save_chat(chat_data):
    """Save chat data to file"""
    chat_id = chat_data['id']
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    with open(chat_path, 'w') as f:
        json.dump(chat_data, f, indent=2)
    
    return chat_id

def load_chat(chat_id):
    """Load chat data from file"""
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    if os.path.exists(chat_path):
        with open(chat_path, 'r') as f:
            return json.load(f)
    return None

def update_chat_title(chat_id, new_title):
    """Update the title of a chat"""
    chat_data = load_chat(chat_id)
    if chat_data:
        chat_data['title'] = new_title
        chat_data['last_updated'] = datetime.datetime.now().isoformat()
        save_chat(chat_data)
        return True
    return False

def delete_chat(chat_id):
    """Delete a chat session"""
    chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    if os.path.exists(chat_path):
        os.remove(chat_path)
        return True
    return False

def add_message_to_chat(chat_id, user_message, bot_message):
    """Add a message pair to the chat history"""
    chat_data = load_chat(chat_id)
    if not chat_data:
        return False
    
    now = datetime.datetime.now().isoformat()
    
    # Update first message as title if this is the first message
    if not chat_data['messages']:
        # Use first 30 chars of user message as title
        title = user_message[:30] + ("..." if len(user_message) > 30 else "")
        chat_data['title'] = title
    
    # Add messages
    chat_data['messages'].append({
        'user': user_message,
        'bot': bot_message,
        'timestamp': now
    })
    
    chat_data['last_updated'] = now
    save_chat(chat_data)
    return True


global assistant, ragproxyagent

# Load custom CSS
def load_css(css_file_paths):
    """Load CSS from multiple files and combine them"""
    css_content = ""
    for css_file_path in css_file_paths:
        try:
            with open(css_file_path, "r") as f:
                css_content += f.read() + "\n"
        except FileNotFoundError:
            print(f"Warning: CSS file {css_file_path} not found")
    return css_content

# Path to CSS files
css_file_path = os.path.join(os.path.dirname(__file__), "chat_ui.css")
dark_theme_extras_path = os.path.join(os.path.dirname(__file__), "dark_theme_extras.css")
try:
    custom_css = load_css([css_file_path, dark_theme_extras_path])
except Exception as e:
    print(f"Error loading CSS: {e}")
    custom_css = ""  # Use empty string if file doesn't exist

with gr.Blocks(css=custom_css) as demo:
    # State variables
    current_chat_id = gr.State("")
    chats_list = gr.State([])
    
    config_list, assistant, ragproxyagent = (
        gr.State(
            [
                {
                    "api_key": "",
                    "api_base": "",
                    "api_type": "azure",
                    "api_version": "2023-07-01-preview",
                    "model": "gpt-35-turbo",
                }
            ]
        ),
        None,
        None,
    )
    assistant, ragproxyagent = initialize_agents(config_list)

    gr.Markdown(
        get_description_text(),
        elem_classes="dark-theme-markdown"
    )
    
    # Define functions for UI interaction
    def refresh_chat_list():
        chats = list_chats()
        return chats, gr.update(choices=[chat["title"] for chat in chats], value=None)
    
    def select_chat(chat_idx, all_chats):
        if chat_idx is None or not all_chats:
            return "", [], ""
        
        # Find the chat by index - chat_idx is the index in the dropdown
        try:
            # Convert to integer if it's a string index
            if isinstance(chat_idx, str):
                # If it's a title, find the matching chat
                for chat in all_chats:
                    if chat["title"] == chat_idx:
                        selected_chat = chat
                        break
                else:
                    # If not found by title, try to find by index if it's a number
                    try:
                        idx = int(chat_idx)
                        if 0 <= idx < len(all_chats):
                            selected_chat = all_chats[idx]
                        else:
                            return "", [], ""
                    except ValueError:
                        return "", [], ""
            else:
                # It's already an integer index
                selected_chat = all_chats[chat_idx]
        except (IndexError, TypeError):
            return "", [], ""
            
        chat_id = selected_chat["id"]
        messages = selected_chat["messages"]
        
        # Format messages for the chatbot
        chat_history = [(msg["user"], msg["bot"]) for msg in messages]
        
        return chat_id, chat_history, selected_chat["title"]
    
    def create_chat():
        new_chat = create_new_chat()
        chats = list_chats()
        # Find the index of the new chat in the list
        new_chat_index = None
        for i, chat in enumerate(chats):
            if chat["id"] == new_chat["id"]:
                new_chat_index = i
                break
        
        return new_chat["id"], [], new_chat["title"], chats, gr.update(choices=[chat["title"] for chat in chats], value=new_chat["title"])
    
    def change_chat_title(chat_id, new_title):
        if not chat_id:
            return None, []
        
        update_chat_title(chat_id, new_title)
        chats = list_chats()
        return chats, gr.update(choices=[chat["title"] for chat in chats])
    
    def delete_current_chat(chat_id, chat_selector, all_chats):
        if not chat_id or not all_chats:
            return "", [], "", all_chats, gr.update(choices=[], value=None)
        
        delete_chat(chat_id)
        chats = list_chats()
        
        if not chats:
            return "", [], "", chats, gr.update(choices=[], value=None)
        
        # Select the first chat if we have chats available
        selected_chat = chats[0]
        chat_history = [(msg["user"], msg["bot"]) for msg in selected_chat["messages"]]
        
        return selected_chat["id"], chat_history, selected_chat["title"], chats, gr.update(choices=[chat["title"] for chat in chats], value=selected_chat["title"])
    
    # Main layout with chat selector on left
    with gr.Row():
        # Left sidebar with chat selection
        with gr.Column(scale=1, elem_classes="chat-selector"):
            gr.Markdown("### Chat Sessions")
            new_chat_btn = gr.Button("+ New Chat", elem_classes="new-chat-btn primary-btn")
            
            chat_dropdown = gr.Dropdown(
                label="Select Chat",
                choices=[],
                interactive=True,
                allow_custom_value=False,
            )
            
            refresh_btn = gr.Button("Refresh", elem_classes="secondary-btn")
            delete_btn = gr.Button("Delete Chat", elem_classes="delete-btn")
            
            chat_title_input = gr.Textbox(
                label="Chat Title",
                placeholder="Enter chat title",
                interactive=True,
            )
            
            rename_btn = gr.Button("Rename", elem_classes="secondary-btn")
        
        # Main chat area
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
                avatar_images=(None, (os.path.join(os.path.dirname(__file__), "autogen.png"))),
                height=600,
            )

            txt_input = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter",
                container=False,
            )

            with gr.Row():
                def update_config(config_list):
                    global assistant, ragproxyagent
                    config_list = autogen.config_list_from_models(
                        model_list=[os.environ.get("MODEL", "gpt-35-turbo")],
                    )
                    if not config_list:
                        config_list = [
                            {
                                "api_key": "",
                                "api_base": "",
                                "api_type": "azure",
                                "api_version": "2023-07-01-preview",
                                "model": "gpt-35-turbo",
                            }
                        ]
                    llm_config = (
                        {
                            "request_timeout": TIMEOUT,
                            # "seed": 42,
                            "config_list": config_list,
                        },
                    )
                    assistant.llm_config.update(llm_config[0])
                    ragproxyagent._model = config_list[0]["model"]
                    return config_list

                def set_params(model, oai_key, aoai_key, aoai_base):
                    os.environ["MODEL"] = model
                    os.environ["OPENAI_API_KEY"] = oai_key
                    os.environ["AZURE_OPENAI_API_KEY"] = aoai_key
                    os.environ["AZURE_OPENAI_API_BASE"] = aoai_base
                    return model, oai_key, aoai_key, aoai_base

                txt_model = gr.Dropdown(
                    label="Model",
                    choices=[
                        "gpt-4",
                        "gpt-35-turbo",
                        "gpt-3.5-turbo",
                    ],
                    allow_custom_value=True,
                    value="gpt-35-turbo",
                    container=True,
                )
                txt_oai_key = gr.Textbox(
                    label="OpenAI API Key",
                    placeholder="Enter key and press enter",
                    max_lines=1,
                    show_label=True,
                    value=os.environ.get("OPENAI_API_KEY", ""),
                    container=True,
                    type="password",
                )
                txt_aoai_key = gr.Textbox(
                    label="Azure OpenAI API Key",
                    placeholder="Enter key and press enter",
                    max_lines=1,
                    show_label=True,
                    value=os.environ.get("AZURE_OPENAI_API_KEY", ""),
                    container=True,
                    type="password",
                )
                txt_aoai_base_url = gr.Textbox(
                    label="Azure OpenAI API Base",
                    placeholder="Enter base url and press enter",
                    max_lines=1,
                    show_label=True,
                    value=os.environ.get("AZURE_OPENAI_API_BASE", ""),
                    container=True,
                    type="password",
                )

            with gr.Row():
                clear = gr.ClearButton([txt_input, chatbot], elem_classes="secondary-btn")

            with gr.Row():
                def upload_file(file):
                    return update_context_url(file.name)

                upload_button = gr.UploadButton(
                    "Upload Context File",
                    file_types=[f".{i}" for i in TEXT_FORMATS],
                    file_count="single",
                )

                txt_context_url = gr.Textbox(
                    label="Enter URL to context file",
                    info=f"File format: [{', '.join(TEXT_FORMATS)}]",
                    max_lines=1,
                    show_label=True,
                    value="https://raw.githubusercontent.com/microsoft/autogen/main/README.md",
                    container=True,
                )

            txt_prompt = gr.Textbox(
                label="Customize Retrieve Agent Prompt",
                max_lines=10,
                show_label=True,
                value=PROMPT_CODE,
                container=True,
                show_copy_button=True,
            )

    # Modified respond function to handle chat saving
    def respond(message, chat_history, chat_id, model, oai_key, aoai_key, aoai_base):
        global config_list
        
        # Handle empty chat_id (no chat selected)
        if not chat_id:
            new_chat = create_new_chat()
            chat_id = new_chat["id"]
            chats = list_chats()
            chat_dropdown_update = gr.update(
                choices=[chat["title"] for chat in chats],
                value=0
            )
        else:
            chat_dropdown_update = gr.update()
        
        # Process the message
        set_params(model, oai_key, aoai_key, aoai_base)
        config_list = update_config(config_list)
        messages = chatbot_reply(message)
        
        # Get the bot response
        bot_message = (
            messages[-1]
            if len(messages) > 0 and messages[-1] != "TERMINATE"
            else messages[-2]
            if len(messages) > 1
            else "Context is not enough for answering the question. Please press `enter` in the context url textbox to make sure the context is activated for the chat."
        )
        
        # Add to chat history
        chat_history.append((message, bot_message))
        
        # Save to chat file
        add_message_to_chat(chat_id, message, bot_message)
        
        # Update chat list and potentially title
        chats = list_chats()
        for i, chat in enumerate(chats):
            if chat["id"] == chat_id:
                title_update = chat["title"]
                break
        else:
            title_update = ""
        
        return "", chat_history, chat_id, title_update, chats, chat_dropdown_update

    def update_prompt(prompt):
        ragproxyagent.customized_prompt = prompt
        return prompt

    def update_context_url(context_url):
        global assistant, ragproxyagent

        file_extension = Path(context_url).suffix
        print("file_extension: ", file_extension)
        if file_extension.lower() not in [f".{i}" for i in TEXT_FORMATS]:
            return f"File must be in the format of {TEXT_FORMATS}"

        if is_url(context_url):
            try:
                file_path = get_file_from_url(
                    context_url,
                    save_path=os.path.join("/tmp", os.path.basename(context_url)),
                )
            except Exception as e:
                return str(e)
        else:
            file_path = context_url
            context_url = os.path.basename(context_url)

        try:
            chromadb.PersistentClient(path="/tmp/chromadb").delete_collection(
                name="autogen_rag"
            )
        except:
            pass
        assistant, ragproxyagent = initialize_agents(config_list, docs_path=file_path)
        return context_url

    # Event handlers for chat functionality
    txt_input.submit(
        respond,
        [txt_input, chatbot, current_chat_id, txt_model, txt_oai_key, txt_aoai_key, txt_aoai_base_url],
        [txt_input, chatbot, current_chat_id, chat_title_input, chats_list, chat_dropdown]
    )
    
    # Chat selection and management
    new_chat_btn.click(
        create_chat,
        [],
        [current_chat_id, chatbot, chat_title_input, chats_list, chat_dropdown]
    )
    
    chat_dropdown.change(
        select_chat,
        [chat_dropdown, chats_list],
        [current_chat_id, chatbot, chat_title_input]
    )
    
    refresh_btn.click(
        refresh_chat_list,
        [],
        [chats_list, chat_dropdown]
    )
    
    delete_btn.click(
        delete_current_chat,
        [current_chat_id, chat_dropdown, chats_list],
        [current_chat_id, chatbot, chat_title_input, chats_list, chat_dropdown]
    )
    
    rename_btn.click(
        change_chat_title,
        [current_chat_id, chat_title_input],
        [chats_list, chat_dropdown]
    )
    
    # Other event handlers
    txt_prompt.submit(update_prompt, [txt_prompt], [txt_prompt])
    txt_context_url.submit(update_context_url, [txt_context_url], [txt_context_url])
    upload_button.upload(upload_file, upload_button, [txt_context_url])
    
    # Initialize chat list on page load
    demo.load(refresh_chat_list, [], [chats_list, chat_dropdown])


if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")
