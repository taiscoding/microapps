# API Key Setup Instructions

## Important Security Notice
The OpenAI API key should never be committed to version control. The application is configured to use an environment variable for the API key.

## Setting Up Your API Key

1. Create or edit the file `radiologytool/key.env` with the following content:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. Replace `your_openai_api_key_here` with your actual OpenAI API key.

3. This file is already added to `.gitignore` to prevent accidental commits.

## Verification

To verify your API key is properly set up:

1. Run the application using:
   ```
   python3 run.py
   ```

2. If you see a warning about no API key found, check that your `key.env` file exists in the correct location with the proper content.

## Security Best Practices

- Never share your API key in public repositories
- Rotate your API keys periodically
- Use environment-specific keys for development and production 