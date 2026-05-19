import os

# 1. extensions/__init__.py
os.makedirs('extensions', exist_ok=True)
with open('extensions/__init__.py', 'w', encoding='utf-8') as f:
    f.write('# Extensions package for LittleGrey\n')
print('created extensions/__init__.py')

# 2. extensions/dialog/__init__.py
os.makedirs('extensions/dialog', exist_ok=True)
with open('extensions/dialog/__init__.py', 'w', encoding='utf-8') as f:
    f.write('from .tokens import DialogToken, TokenType\n')
    f.write('from .parser import DialogParser\n')
    f.write('from .handlers import MessageHandler, HandlerChain\n')
print('created extensions/dialog/__init__.py')

# 3. extensions/memory_enhanced/__init__.py
os.makedirs('extensions/memory_enhanced', exist_ok=True)
with open('extensions/memory_enhanced/__init__.py', 'w', encoding='utf-8') as f:
    f.write('# Memory enhancement module\n')
print('created extensions/memory_enhanced/__init__.py')

print('All init files created')
