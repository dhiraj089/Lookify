import re

file_path = r"d:/Lookify/Frontend/server.py"

with open(file_path, 'r') as f:
    content = f.read()

# 1. Update /api/signup
# Using a simpler match that just looks for the email line within the signup block
signup_block_match = re.search(r"@app\.route\('/api/signup'.*?def signup.*?\n(.*?)(?=@app\.route|$)", content, re.DOTALL)
if signup_block_match:
    block = signup_block_match.group(0)
    new_block = re.sub(r"email = data\.get\('email'\)", "email = data.get('email', '').strip().lower()\n        data['email'] = email", block)
    content = content.replace(block, new_block)

# 2. Update /api/update_user
update_block_match = re.search(r"@app\.route\('/api/update_user'.*?def update_user.*?\n(.*?)(?=@app\.route|$)", content, re.DOTALL)
if update_block_match:
    block = update_block_match.group(0)
    new_block = re.sub(r"email = data\.get\('email'\)", "email = data.get('email', '').strip().lower()\n        data['email'] = email", block)
    content = content.replace(block, new_block)

with open(file_path, 'w') as f:
    f.write(content)

print("Successfully updated server.py using improved regex.")
