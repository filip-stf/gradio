# AutoGen Chat Demo with Multi-Chat Support

This enhanced version of the AutoGen Retrieve Chat Demo adds a chat selection panel on the left side, allowing users to:

- Create new chat sessions
- Switch between existing chat sessions
- Rename chat sessions
- Delete chat sessions

## Features

- **Chat Selection Panel**: Located on the left side, allows easy navigation between different conversations
- **Persistent Chat History**: All chats are saved to disk and can be resumed later
- **Automatic Chat Naming**: New chats are automatically named based on the first message
- **Custom Styling**: UI is enhanced with custom CSS for better visual appeal

## Usage

1. **Starting a New Chat**:
   - Click the "+ New Chat" button to start a fresh conversation

2. **Switching Between Chats**:
   - Use the dropdown menu to select a previous chat session
   - Click "Refresh" to update the list if needed

3. **Renaming a Chat**:
   - Select a chat from the dropdown
   - Enter a new title in the "Chat Title" field
   - Click "Rename" to save the new title

4. **Deleting a Chat**:
   - Select the chat you want to delete
   - Click the "Delete Chat" button
   - Confirm if prompted

5. **Working with the Chatbot**:
   - Type messages in the input field at the bottom
   - Upload context files or provide URLs to help the bot with specific knowledge
   - Customize the retrieval prompt if needed

## Technical Details

- Chats are stored as JSON files in the `/workspaces/gradio/chats` directory
- CSS styling is provided in the `chat_ui.css` file
- The chat panel uses Gradio's column and row components for layout

## Customization

You can further customize the UI by modifying the `chat_ui.css` file. Key CSS classes include:

- `.chat-selector`: Styles the left sidebar
- `.chat-item`: Styles individual chat items in the list
- `#chatbot`: Styles the main chat display
- `.user` and `.bot`: Style the user and bot messages

## Running the App

```bash
python app.py
```

This will start the Gradio server and make the app available at the specified address (typically localhost:7860 or a public URL if sharing is enabled).
