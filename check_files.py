with open(r'e:\coding-zhou\Python\feedback.html', 'r', encoding='utf-8') as f:
    orig = f.read()
with open(r'e:\coding-zhou\Python\public\feedback\index.html', 'r', encoding='utf-8') as f:
    pub = f.read()
print(f'Original: {len(orig)} chars')
print(f'Public: {len(pub)} chars')
print(f'Match: {orig == pub}')

if 'onsubmit="submitFeedback' in pub:
    print('WARNING: public/feedback/index.html still has old onsubmit!')
else:
    print('OK: old onsubmit removed')

if 'DOMContentLoaded' in pub:
    print('OK: new DOMContentLoaded code present')
else:
    print('WARNING: DOMContentLoaded not found!')