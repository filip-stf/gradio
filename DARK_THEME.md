# Dark Theme Customization for AutoGen Chat UI

This document explains the dark theme implementation for the AutoGen Chat Demo application.

## Overview

The dark theme provides a modern, eye-friendly interface with dark backgrounds and appropriate contrast for all UI elements. The implementation consists of:

1. A primary CSS file (`chat_ui.css`) with dark mode styling
2. Supplementary dark theme overrides (`dark_theme_extras.css`) for additional Gradio components
3. CSS class additions to key elements to ensure proper dark mode rendering

## Key Features

- **Dark backgrounds** for all UI containers and components
- **Appropriate text contrast** for better readability
- **Custom scrollbars** styled to match the dark theme
- **Message bubbles** with color-coded backgrounds (blue for user, dark gray for bot)
- **Form controls** (buttons, inputs, dropdowns) styled for dark mode
- **Custom styling** for Markdown content

## Implementation Details

### Main Container Styling

The main Gradio container and page background are set to dark colors:

```css
.gradio-container {
    background-color: #1e1e1e !important;
    color: #e0e0e0 !important;
}

body {
    background-color: #1e1e1e !important;
}
```

### Chat Selector Panel

The left sidebar with chat selection features has a slightly lighter background than the main container:

```css
.chat-selector {
    background-color: #252525;
    border-right: 1px solid #333;
}
```

### Message Styling

User and bot messages have distinct colors:

```css
#chatbot .user {
    background-color: #0c4a6e !important;
    color: #ffffff !important;
}

#chatbot .bot {
    background-color: #3a3a3a !important;
    color: #e0e0e0 !important;
}
```

### Form Controls

Inputs, textareas, and buttons have been styled to match the dark theme:

```css
textarea {
    background-color: #2d2d2d !important;
    color: #e0e0e0 !important;
    border: 1px solid #444 !important;
}

.secondary-btn {
    background-color: #333333 !important;
    color: #e0e0e0 !important;
}
```

### Markdown Content

Special classes are applied to markdown content to ensure readability:

```css
.dark-theme-markdown h1 {
    color: #e0e0e0 !important;
    border-bottom: 1px solid #444;
}

.dark-theme-markdown a {
    color: #3b9cff !important;
}
```

## Additional Overrides

The `dark_theme_extras.css` file contains additional overrides for Gradio components that might not be covered by the main CSS:

```css
.gr-dropdown, .gr-form, select, option {
    background-color: #2d2d2d !important;
    color: #e0e0e0 !important;
}

.markdown-body {
    background-color: transparent !important;
    color: #e0e0e0 !important;
}
```

## How to Modify the Theme

To make further adjustments to the dark theme:

1. Edit `chat_ui.css` for changes to the main layout components
2. Edit `dark_theme_extras.css` for overrides to specific Gradio components
3. Use browser dev tools to identify additional elements that need styling

## Color Palette

The dark theme uses the following color palette:

- **Background Colors**:
  - Main background: `#1e1e1e`
  - Panel background: `#252525`
  - Control background: `#2d2d2d`
  - Chat message (bot): `#3a3a3a`
  - Chat message (user): `#0c4a6e`

- **Text Colors**:
  - Primary text: `#e0e0e0`
  - Secondary text: `#cccccc`
  - Links: `#3b9cff`

- **Border Colors**:
  - Primary border: `#333`
  - Secondary border: `#444`

## Loading the CSS

The application loads both CSS files and combines them:

```python
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

custom_css = load_css([css_file_path, dark_theme_extras_path])
```
