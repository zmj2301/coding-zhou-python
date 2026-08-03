import re

p = '/etc/nginx/conf.d/code-explorer.conf'
s = open(p, encoding='utf-8').read()

fb_block = '''    location = /feedback {
        rewrite ^ /feedback.html permanent;
    }

'''

old_console = '''    location = /console {
        rewrite ^ /console.html permanent;
    }
'''

new_console = old_console + fb_block

count = s.count(old_console)
s = s.replace(old_console, new_console)
open(p, 'w', encoding='utf-8').write(s)
print('console blocks replaced:', count)
print('feedback blocks:', s.count('location = /feedback'))
