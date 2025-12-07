#!/bin/bash
# Script to add SSH key to VM
# Run this ON THE VM after logging in

echo "🔑 Adding SSH key to authorized_keys..."
echo ""

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the public key
PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDCX9AwfOw4z+v0lTENkj8L5h56JoTpl0ZZa4N9PAO62QP0gjqLheR2HtvEJViYgJEK6R51biNcL6LD8EgCKCUVBTYIIB6eoq4qOcct2BjXd1aZ869XWMs9kaJ3I3n7nc/DtZ49cH0D9ux90ocbWWVB937ZEJQ3nAVqvC1A8woKKTw8D5MzfGod/3A0k0YAP55hX25vLxonuAZGtFKenfm7waUuFrAbfXxaMbhB5mSlac/dlm+EbH/dJ1+HOXdZIdAlTwvIZpXhqENG76hx0XlrAxw4cGSdVFgvUofFHe0XmOKV52UCnVXkTAv3GvzSoxjOvDoKJmTpXVFKrMO86AWzfLmD3WTH0wgYFEUBd5fvLX75QGrhvYlS9eR5eHyTbvo1cKkThoHSEFKeJCGgG01uXY21MbcL4ninGNQJVSbV7XT5RrLKBN/UyAhXbQa05QofmOnPWgS2nYO3ZQYd5fRly9Lja7y8WyfZdkI8GVYaY/YemqYj3w4qdeM4pvOvD5FwcpIXTinX6lxWzrDrDYs2isuB2In1lbhw31CQD7AFGaskKTRFmOqdDi02D7LEPpeK7Tv5cZR0iafmVL4Ue/EcclpVSW84V68lXOaq4i04+t4Y7qv4B5w6nLOtr2wSjrt2QjwoM3pUgszDltLuFjL5ptRaT38n43sq1T9jt0T2dw== cursor-ai-access"

# Check if key already exists
if grep -q "cursor-ai-access" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "⚠️  Key already exists in authorized_keys"
    echo "   Skipping addition..."
else
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    echo "✅ SSH key added successfully!"
fi

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys

echo ""
echo "✅ Setup complete!"
echo ""
echo "You can now connect with:"
echo "  ssh -i ~/.ssh/vm_access_key likithashankar14@136.112.137.224"
echo ""

