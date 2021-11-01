import sublime, sublime_plugin
import string, random, os.path

# Python 2
try:
  import urllib2

# Python 3
except ImportError:
  import urllib.request as urllib2

class FilePart:
  CONTENT_TRANSFER_ENCODING = 'utf-8'

  def __init__(self, name, filename, body, boundary):
    self.name = name
    self.filename = filename
    self.body = body
    self.boundary = boundary
    self.headers = {
      # Needs to be text/plain content type otherwise the file will get downloaded by browser
      'Content-Type': 'text/plain;charset=utf-8;',

      'Content-Disposition': 'form-data; name="{0}"; filename="{1}"'.format(self.name, self.filename),
      'Content-Transfer-Encoding': self.CONTENT_TRANSFER_ENCODING,
    }

  def get(self):
    lines = []
    lines.append('--' + self.boundary)

    for key, val in self.headers.items():
      lines.append('{0}: {1}'.format(key, val))

    lines.append('')
    lines.append(self.body)
    lines.append('--{0}--'.format(self.boundary))
    lines.append('')

    return lines

class FileForm:
  NEW_LINE = '\r\n'

  # Generate a random boundary
  def _gen_boundary(self):
    chars = string.ascii_lowercase + string.digits

    return ''.join(random.choice(chars) for x in range(40))

  def __init__(self):
    self.boundary = self._gen_boundary()
    self._file = None

  def file(self, filename, content):
    # Needs to be submitted under 'file'. Other supported names are: url, shorten
    self._file = FilePart('file', filename, content, self.boundary)

  def get(self):
    # File returns an array
    content = self._file.get()

    content_type = 'multipart/form-data; boundary=' + self.boundary

    return content_type, self.NEW_LINE.join(content).encode(FilePart.CONTENT_TRANSFER_ENCODING)

# Can also be tested in console by running `view.run_command('post0x0')`
class Post0x0Command(sublime_plugin.TextCommand):
  def _get_file_name(self):
    name = 'untitled'

    try:
        name = os.path.split(self.view.file_name())[-1]
    except AttributeError:
        pass
    except TypeError:
        pass

    return name

  def run(self, edit):
    # Init an empty unicode string
    content = u''

    # Loop over the selections in the view
    for region in self.view.sel():
      if not region.empty():
        # Be sure to insert a newline if we have multiple selections
        if content:
          content += FileForm.NEW_LINE

        content += self.view.substr(region)

    # If we havent gotten data from selected text, we assume the entire file should be pasted
    if not content:
      content += self.view.substr(sublime.Region(0, self.view.size()))

    filename = self._get_file_name()

    # Build our virtual file that will hold the content
    form = FileForm()
    form.file(filename = filename, content = content)

    content_type, body = form.get()

    # Post the file to 0x0
    request = urllib2.Request(url = 'https://0x0.st', headers = { 'Content-Type': content_type }, data = body)
    response = urllib2.urlopen(request).read().decode(FilePart.CONTENT_TRANSFER_ENCODING)

    # Response is the URL to the content
    sublime.set_clipboard(response)
    sublime.status_message("Copied: {0}".format(response))


