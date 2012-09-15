from xml.dom import minidom
from datetime import datetime
import string, argparse, urllib2, urllib, base64, os

class Convert:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description='Convert JSKit Xml to Echo2 format', prog='Social Conversion')
		self.parser.add_argument('--s', action='store_true', help='send to echo')
		self.parser.add_argument('--file', default='', help='name of single file to process')
		self.parser.add_argument('--input_path', default='./', help='location of files to process')
		self.parser.add_argument('--output_path', default='', help='write xml to this file')
		arg_list = self.parser.parse_args()
		self.file = arg_list.file
		self.inputPath = arg_list.input_path
		self.outputPath = arg_list.output_path
		self.sendToEcho = arg_list.s
		
	def log(self, txt):
		print txt, '. . .'

	def GetActor(self, jsKitAttributes, author, domain=''):
		objectType = self.AddTag('activity:object-type', 'http://activitystrea.ms/schema/1.0/person')
		if (author != 'Guest Commenter'):
			userId = self.AddTag('id', self.FixUserUrl(self.GetValueByKey(jsKitAttributes,'user_identity')))
		else:
			userId = self.AddTag('id', domain + '/user/guest')
		title = self.AddTag('title', author)
		return self.AddTag('activity:actor', objectType + userId + title)
		
	def GetActivityVerb(self):
		return self.AddTag('activity:verb', 'http://activitystrea.ms/schema/1.0/post')

	def GetActivityObject(self, comment, id):
		innerXml = self.AddTag('activity:object-type', 'http://activitystrea.ms/schema/1.0/comment')
		innerXml += self.AddTagWithAttributes('content', self.EscapeHtmlContent(comment), ['type'], ['html'])
		innerXml += self.AddTag('id', id)
		innerXml += self.AddTag('echo:status', 'Untouched')
		return self.AddTag('activity:object', innerXml)
		
	def GetActivityTarget(self, parent):
		innerXml = self.AddTag('id', parent)
		innerXml += self.AddTag('activity:object-type','http://activitystrea.ms/schema/1.0/article')
		return self.AddTag('activity:target', innerXml)
		
	def GetParent(self, xml, stream, domain):
		node = xml.getElementsByTagName('jskit:parent-guid')
		if (len(node) > 0):
			return domain + stream + '/' + node[0].firstChild.data
		return domain + stream
		
	def GetEchoXml(self, xml, domain):
		if xml == '':
			return []
		xmlArray = []
		xml = minidom.parseString(xml)
		newXml = '<feed xlmns="http://www.w3.org/2005/Atom" xmlns:echo="http://js-kit.com/spec/e2/v1" xmlns:activity="http://activitystrea.ms/spec/1.0/">'
		channelList = xml.tn('channel')
		itemCount = 0
		for channel in channelList:
			stream = channel.tn('jskit:attribute',0).attributes['value'].value
			itemList = channel.tn('item')
			for item in itemList:
				itemId = domain + stream  + '/' + item.getElementsByTagName('guid')[0].firstChild.data
				jsKitAttributes = item.getElementsByTagName('jskit:attribute');
				newXml += '<entry>'
				newXml += self.AddTag('id', itemId)
				publishedValue = item.getElementsByTagName('pubDate')[0].firstChild.data
				newXml += self.AddTag('published', self.ConvertDate(publishedValue))
				try: newXml += self.GetActor(jsKitAttributes, item.getElementsByTagName('author')[0].firstChild.data)
				except IndexError:
					newXml += self.GetActor(jsKitAttributes, 'Guest Commenter',domain)
				newXml += self.GetActivityVerb()
				newXml += self.GetActivityObject(item.getElementsByTagName('description')[0].firstChild.data, itemId)
				newXml += self.GetActivityTarget(self.GetParent(item, stream, domain))
				newXml += '</entry>'
				itemCount+=1
				if(itemCount == 100):
					newXml+= '</feed>'
					xmlArray.append(minidom.parseString(newXml))
					newXml = '<feed xlmns="http://www.w3.org/2005/Atom" xmlns:echo="http://js-kit.com/spec/e2/v1" xmlns:activity="http://activitystrea.ms/spec/1.0/">'
		newXml += '</feed>'
		xmlArray.append(minidom.parseString(newXml))
		return xmlArray
		
	def GetEchoXmlFromFile(self,filePath):
		with open(filePath, 'r') as old:
			xml = old.read()
		old.close()

		return self.GetEchoXml(xml, self.GetDomainFromFileName(filePath))
		
	def GetEchoXmlFromFiles(self, fileList):
		xmlList = []
		for file in fileList:
			xmlList.extend(self.GetEchoXmlFromFile(file))
		return xmlList
	
	def GetDomainFromFileName(self, filePath):
		return 'http://' + filePath[filePath.rfind('/')+1:-13]
		
	def GetListOfFiles(self,path):
		return os.listdir(path)

	def AddTag(self, tag, value):
		return '<{0}>{1}</{0}>'.format(tag, value)

	def AddTagWithAttributes(self, tag, value, attr, attrValues):
		encoded = value.encode('utf-8').replace('<', '&amp;lt;').replace('>', '&amp;gt;')
		xml = '<' + tag
		for x, y in zip(attr, attrValues):
			xml += ' {0}="{1}"'.format(x, y)
		xml += '>{0}</{1}>'.format(encoded, tag)
		return xml
		
	def ConvertDate(self, jskitDate):
		return datetime.strptime(jskitDate,'%a, %d %b %Y %H:%M:%S +0000').strftime('%Y-%m-%dT%H:%M:%S.000Z')
		
	def EscapeHtmlContent(self, content):
		return content.replace('&','&amp;')

	def GetValueByKey(self, elementList,  key):
		for el in elementList:
			if(el.attributes['key'].value == key):
				return el.attributes['value'].value
		return ''

	def FixUserUrl(self, url):
		return url[string.find(url,"http"):-1]
		
	def SendCommentsToEcho(self, xml):
		values = { 'content': xml.toxml(encoding='utf-8'), 'mode':'replace' }
		data = urllib.urlencode(values)
		request = urllib2.Request('https://api.echoenabled.com/v1/submit', data)
		base64string = base64.encodestring('%s:%s' % ('username', 'password'))[:-1]
		authheader =  "Basic %s" % base64string
		request.add_header("Authorization", authheader)
		response = urllib2.urlopen(request)
		return response.read()
		
	def MagicHappensHere(self, xmlList):
		if (self.sendToEcho == True):
			self.log('Sending Comments to Echo')
			for xml in xmlList:
				self.log('Sending chunk to Echo')
				result = self.SendCommentsToEcho(xml)
				self.log('Response:' + result)
		if (self.outputPath != ''):
			self.log('Writing to file')
			file = open(self.outputPath, 'w')
			for xml in xmlList:
				file.write(xml.toprettyxml(encoding='utf-8'))
			file.close()


	def Run(self):
		self.log('Starting')
		xmlList = []
		if (self.file != ''):
			filePath = self.inputPath + self.file
			self.log('Working on 1 file:' + filePath)
			xmlList.extend(self.GetEchoXmlFromFile(filePath))
		else:
			fileList = self.GetListOfFiles(self.inputPath)
			self.log('Working on a bunch of files: ' + str(len(fileList)))
			for aFile in fileList:
				self.log(aFile)
				xmlList.extend(self.GetEchoXmlFromFile(self.inputPath + aFile))
		self.MagicHappensHere(xmlList)
			
def tn(self,tagname,idx=-1):
	if(idx==-1):
		return self.getElementsByTagName(tagname)
	else:
		return self.getElementsByTagName(tagname)[idx]

def data(self):
	return self.firstChild.data
	
minidom.Document.tn = tn
minidom.Document.data = data
minidom.Element.tn = tn
minidom.Element.data = data
			
if __name__ == '__main__':
	processor = Convert()
	processor.Run()
