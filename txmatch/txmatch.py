import re
import fileinput

start_marker = re.compile("OnBeginRequest:")
end_marker = re.compile("OnEndRequest:")
request_id = re.compile("\[(\d+)\].*SessionID: (\w+)")

class NoIdInString(Exception):
    pass

class BeginEndMatcher(object):
    def __init__(self):
        self.on_begin_detected = 0
        self.on_end_detected = 0
        self.requests = {}

    def process(self, line_iterator):
        for line in line_iterator:
            if line:
                self.process_one_line(line)

    def get_request_id_for_line(self, line):
        match =  request_id.search(line)
        if not match:
            raise NoIdInString(line)
        return match.groups()

    def process_one_line(self, line):
        if start_marker.search(line):
            try:
                self.on_begin_detected = 1
                id = self.get_request_id_for_line(line)
                self.installActivity('start',id, line)
            except:
                pass
        if end_marker.search(line):
            try:
                self.on_end_detected = 1
                id = self.get_request_id_for_line(line)
                self.installActivity('end', id, line)
            except:
                pass

    def installActivity(self, activity, id, line):
        self.requests \
            .setdefault(id,[]) \
            .append((activity,line))

    def incompleteRequests(self):
        extras = []
        for (key,activities) in self.requests.iteritems():
            localstack = []
            for activity in activities:
                (type,line) = activity
                if type == 'start':
                    localstack.append(activity)
                if type == 'end':
                    if len(localstack) != 0:
                        localstack.pop()
            extras += [ reformatLine(line) for (type,line) in localstack]
        return extras 


def main():
    processor = BeginEndMatcher()
    processor.process(lineGenerator())
    for line in  processor.incompleteRequests():
        print line

def lineGenerator():
    reader = fileinput.input(openhook=fileinput.hook_compressed)
    for line in reader:
        yield "%s(%d): %s" % (fileinput.filename(), fileinput.filelineno(), line)


url_match = re.compile("CurrentURL:\s*([^,]*)")
def reformatLine(text):
    (locator,line) = text.split(':',1)
    (date,time) = line.split()[0:2]
    (pid, sessionid) = request_id.search(line).groups()
    [username] = re.search("{([^}]*)}", line).groups()
    [url] = url_match.search(line).groups()
    return " ".join( [date,time,sessionid,pid,username,url,locator] )

if __name__ == "__main__":
    main()
