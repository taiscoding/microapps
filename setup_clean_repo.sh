#!/bin/bash

# Display information about what this script does
echo "This script will set up a clean Git repository for your MicroApps project."
echo "It will remove the existing .git directory and any sensitive files."
echo ""
echo "IMPORTANT: Make sure you have backed up any important data before proceeding."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

# Remove existing .git directory
echo "Removing existing Git repository..."
rm -rf .git

# Remove any other unwanted files
echo "Removing unneeded files..."
rm -f necessary necessary.pub "ssh-keygen -t ed25519 -C \"your-email@example.com\""

# Create key.env from example if it doesn't exist
if [ ! -f radiologytool/key.env ]; then
    echo "Creating radiologytool/key.env from example..."
    cp radiologytool/key.env.example radiologytool/key.env
    echo "IMPORTANT: Edit radiologytool/key.env to add your API key."
fi

# Initialize new Git repository
echo "Initializing new Git repository..."
git init

# Show next steps
echo ""
echo "Clean repository set up successfully!"
echo ""
echo "Next steps:"
echo "1. Edit radiologytool/key.env to add your OpenAI API key"
echo "2. Make your first commit with:"
echo "   git add ."
echo "   git commit -m \"Initial commit\""
echo "3. Add your remote with:"
echo "   git remote add origin your-repository-url"
echo "4. Push your code with:"
echo "   git push -u origin main"
echo ""
echo "Then run the app with: python3 run.py" 