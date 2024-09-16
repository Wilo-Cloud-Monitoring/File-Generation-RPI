#!/bin/bash

# Define the file path for the SSH keys
SSH_KEY_PATH="$HOME/.ssh/id_rsa"

# Check if the SSH key already exists
if [ -f "$SSH_KEY_PATH" ]; then
    echo "SSH key already exists at $SSH_KEY_PATH"
else
    # Generate a new SSH key without a passphrase
    echo "Generating new SSH deploy key..."
    ssh-keygen -t rsa -b 4096 -C "deploy_key_for_rpi" -f "$SSH_KEY_PATH" -N ""

    echo "SSH key generated successfully."
fi

# Display the public key
echo "Your public key is:"
cat "$SSH_KEY_PATH.pub"

echo ""
echo "Copy the above public key and add it to your GitHub repository as a deploy key."
echo "Go to repository > Settings > Deploy Keys"