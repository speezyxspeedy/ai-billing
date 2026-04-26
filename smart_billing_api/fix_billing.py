import re

# Fix script.js - make billing tab always visible
with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_js = """  const softwareTabs = document.querySelectorAll('.software-tab');
  softwareTabs.forEach(tab => {
    tab.style.display = isLoggedIn ? 'flex' : 'none';
  });"""

new_js = """  const softwareTabs = document.querySelectorAll('.software-tab');
  softwareTabs.forEach(tab => {
    if (tab.dataset.page === 'billing') {
      tab.style.display = 'flex';
    } else {
      tab.style.display = isLoggedIn ? 'flex' : 'none';
    }
  });"""

content = content.replace(old_js, new_js)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('script.js updated')

# Fix ai_billing.html - make billing the default visible page
with open('ai_billing.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'class="nav-tab software-tab" data-page="billing" style="display: none;"',
    'class="nav-tab software-tab active" data-page="billing"'
)

content = content.replace(
    'class="nav-tab active" data-page="login"',
    'class="nav-tab" data-page="login"'
)

content = content.replace(
    'id="page-login" class="page active"',
    'id="page-login" class="page"'
)

content = content.replace(
    'id="page-billing" class="page"',
    'id="page-billing" class="page active"'
)

content = content.replace('</head>\n</head>', '</head>')

with open('ai_billing.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('ai_billing.html updated')
