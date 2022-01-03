import requests
import browser_cookie3
from lxml import html
import shutil
import os
from slugify import slugify
import functools

baseurl = "https://canvas.cornell.edu"
cj = browser_cookie3.chrome(domain_name="canvas.cornell.edu")
cwd = os.getcwd()

class CoursesPage:
	def __init__(self):
		resp = requests.get(f"{baseurl}/courses", cookies=cj)
		tree = html.fromstring(resp.content)
		self.course_links = tree.xpath('//*[@id="my_courses_table"]/tbody/tr/td/a')
		self.course_links += tree.xpath('//*[@id="past_enrollments_table"]/tbody/tr/td/a')

	def getCourses(self):
		acc = []
		for course_link in self.course_links:
			acc.append(Course(course_link))
		return acc

	def download(self):
		newpath = os.path.join(cwd, 'courses')
		# if not os.path.exists(newpath):
		# 	os.makedirs(newpath)
		for course in self.getCourses():
			course.download(newpath)


class Course:
	def __init__(self, course_link):
		self.href = course_link.get("href")
		self.name = course_link.get("title")
		self.page = None

	def __str__(self):
		return f"<{self.name}, {self.href}>"

	def getPage(self):
		if self.page:
			return self.page
		else:
			self.page = requests.get(f"{baseurl}/{self.href}/modules", cookies=cj)
			return self.page

	def tree(self):
		return html.fromstring(self.getPage().content)

	def modules(self):
		acc = []
		context_modules = self.tree().xpath('//*[@id="context_modules"]/div')
		for module in context_modules:
			label = module.get('aria-label')
			content = module.find('div[2]/ul')
			acc.append(Module(label, content.getchildren()))
		return acc

	def download(self, path):
		newpath = os.path.join(path, slugify(self.name))
		# if not os.path.exists(newpath):
		# 	os.makedirs(newpath)
		for module in self.modules():
			module.download(newpath)


class Module:
	def __init__(self, title, items):
		self.title = title
		self.items = items

	def __str__(self):
		return f"<{self.title}, {self.items}>"

	def _attachments(self):
		acc = []
		for item in self.items:
			if item.cssselect('.attachment'):
				acc.append(item)
		return acc

	def documents(self):
		acc = []
		for attachment in self._attachments():
			anchor = attachment.cssselect('a.for-nvda')[0]
			acc.append(Document(anchor.text.strip(), anchor.get('href')))
		return acc

	def _urls(self):
		acc = []
		for item in self.items:
			if item.cssselect('.external_url'):
				acc.append(item)
		return acc

	def externallinks(self):
		acc = []
		for url in self._urls():
			anchor = url.cssselect('a.external_url_link')[0]
			acc.append(ExternalLink(anchor.get('title'), anchor.get('href')))
		return acc

	def download(self, path):
		newpath = os.path.join(path, slugify(self.title))
		# if not os.path.exists(newpath):
		# 	os.makedirs(newpath)
		for document in self.documents():
			document.download(newpath)

class Document:
	def __init__(self, title, href):
		self.href = href
		self.page = None
		self.title = self.tree().xpath('//*[@id="content"]/h2')[0].text

	def __str__(self):
		return f"<{self.title}, {self.href}>"

	def getPage(self):
		if self.page:
			return self.page
		else:
			self.page = requests.get(f"{baseurl}/{self.href}", cookies=cj)
			return self.page

	def tree(self):
		return html.fromstring(self.getPage().content)

	def _downloadlink(self):
		anchor = self.tree().xpath('//*[@id="content"]/div[1]/span/a')[0]
		return anchor.get('href')

	def _title(self):
		dot = self.title.rfind(".")
		fronthalf = slugify(self.title[:dot])[:155]
		title = fronthalf + self.title[dot:]
		return title

	def download(self, path):
		outputpath = os.path.join(path, self._title())
		if not os.path.exists(path):
			os.makedirs(path)
		if not os.path.exists(outputpath):
			print(f"Downloading {self._title()}")
			with requests.get(f"{baseurl}/{self._downloadlink()}", cookies=cj, stream=True) as r:
				r.raw.read = functools.partial(r.raw.read, decode_content=True)
				with open(outputpath, 'wb') as f:
					shutil.copyfileobj(r.raw, f)
		else:
			print(f"Skipping {self._title()}")


class ExternalLink:
	def __init__(self, title, url):
		self.title = title
		self.url = url

	def __str__(self):
		return f"<{self.title}, {self.url}>"

cp = CoursesPage()
cs = cp.getCourses()

cp.download()

# for c in cs:
# 	if(c.href == '/courses/30147'):
# 		c.download(os.path.join(cwd, 'courses'))
# 		modules = c.modules()
# 		for module in modules:
# 			for document in module.documents():
# 				if(document.title == 'Ch4_BirthNewborn.pdf'):
# 					print(document)
# 					print(document.getPage())
# 					document.download()


