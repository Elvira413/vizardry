
import setuptools

def readme():
  with open('README.md', encoding='utf8') as fp:
    return fp.read()

def requirements():
  with open('requirements.txt') as fp:
    return fp.readlines()

setuptools.setup(
  name = 'vizardry',
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  long_description = readme(),
  long_description_content_type = 'text/markdown',
  install_requires = requirements(),
  packages = setuptools.find_packages(),
  entry_points = {
    'console_scripts': [
      'vizardry = vizardry.main:main'
    ]
  }
)
