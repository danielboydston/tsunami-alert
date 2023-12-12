from html.parser import HTMLParser
import re

class BulletinHTMLParser(HTMLParser):

  def __init__(self):
    super(BulletinHTMLParser, self).__init__()
    self.field_list: list[str] = []
    self.in_thead: bool = False
    self.in_th: bool = False
    self.in_td: bool = False
    self.in_a: bool = False
    self.cur_record: list[str] = []
    self.cur_field = {}
    self.cur_link = {}
    self.items: list = []

  def handle_starttag(self, tag, attrs):
    if tag == "thead":
      self.in_thead = True
    elif tag == "th":
      self.in_th = True
    elif tag == "td":
      self.in_td = True
      self.cur_field = {}
    elif tag == "a":
      self.in_a = True
      for attr in attrs:
        if attr[0] == "href":
          self.cur_link['href'] = attr[1]
    elif tag == "tr" and self.in_thead == False:
      self.cur_record = []
    print(f"start {tag}")

  def handle_endtag(self, tag):
    if tag == "thead":
      self.in_thead = False
    elif tag == "th":
      self.in_th = False
    elif tag == "td":
      self.in_td = False
      self.cur_record.append(self.cur_field)
      print(f"appending to cur_record {self.cur_field}")
    elif tag == "a":
      self.in_a = False
      self.cur_field['link'] = self.cur_link
      self.cur_link = {}
    elif tag == "tr" and self.in_thead == False:
      self.items.append(self.cur_record)
    print(f"end {tag}")

  def handle_data(self, data):
    if self.in_th:
      self.field_list.append(data.strip())
    elif self.in_td:
      data = data.strip()
      if len(data) > 0:
        self.cur_field['text'] = data
        